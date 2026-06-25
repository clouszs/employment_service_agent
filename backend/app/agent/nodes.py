"""Agent 节点实现：路由、检索、置信度检查、生成、拒答等。"""

from __future__ import annotations

import logging
from typing import Any

from app.agent.constants import (
    CITATION_SNIPPET_MAX_LENGTH,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    HIGH_RISK_KEYWORDS,
    LOW_RISK_KEYWORDS,
    TOOL_KEYWORDS,
)
from app.agent.citation_tracker import build_citations
from app.agent.hallucination_defense import (
    consistency_checker,
    fact_verifier,
    threshold_checker,
)
from app.agent.prompts.generator import GENERATOR_SYSTEM_PROMPT, GENERATOR_USER_PROMPT
from app.agent.prompts.regenerator import REGENERATOR_SYSTEM_PROMPT, REGENERATOR_USER_PROMPT
from app.agent.prompts.router import ROUTER_SYSTEM_PROMPT, ROUTER_USER_PROMPT
from app.agent.refusal_handler import get_refusal_response
from app.agent.temporal_retriever import apply_temporal_adjustment, filter_expired_docs
from app.agent.tools import ToolCallTracker, knowledge_search
from app.core.config import settings
from app.core.llm import chat_with_usage
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


# ==================== 工具选择循环防护：关键词路由 ====================


def route_query(state: dict) -> dict:
    """路由决策节点：search / direct / refuse。

    防工具选择循环：tool_call_count >= 3 时强制生成。
    """
    query = state.get("current_query", "")
    tool_count = state.get("tool_call_count", 0)

    # 工具选择循环防护：强制退出
    if tool_count >= 3:
        logger.warning("路由节点：工具调用次数(%d)已达上限，强制生成", tool_count)
        return {
            "route": "generate",
            "forced_exit": True,
            "reasoning_chain": state.get("reasoning_chain", []) + [
                {"step": "route", "decision": "forced_exit", "reason": f"tool_call_count={tool_count}>=3"},
            ],
        }

    # 低风险关键词：直接回复
    if any(k in query for k in LOW_RISK_KEYWORDS):
        return {
            "route": "direct",
            "query_risk_level": "low",
            "reasoning_chain": state.get("reasoning_chain", []) + [
                {"step": "route", "decision": "direct", "reason": "低风险问候"},
            ],
        }

    # 高风险关键词：检索 + 高置信度要求
    if any(k in query for k in HIGH_RISK_KEYWORDS):
        return {
            "route": "search",
            "query_risk_level": "high",
            "reasoning_chain": state.get("reasoning_chain", []) + [
                {"step": "route", "decision": "search", "reason": "高风险政策查询"},
            ],
        }

    # 工具调用关键词：走检索
    if any(k in query for k in TOOL_KEYWORDS):
        return {
            "route": "search",
            "query_risk_level": "medium",
            "reasoning_chain": state.get("reasoning_chain", []) + [
                {"step": "route", "decision": "search", "reason": "中等风险查询"},
            ],
        }

    # 默认：检索
    return {
        "route": "search",
        "query_risk_level": "medium",
        "reasoning_chain": state.get("reasoning_chain", []) + [
            {"step": "route", "decision": "search", "reason": "默认路由"},
        ],
    }


# ==================== 检索节点（带去重）====================


def search_knowledge(state: dict) -> dict:
    """时效感知检索节点。

    防工具选择循环：相同查询不重复检索。
    V1 简化：仅做过期文档标记，不做完整时效性评分。
    """
    query = state.get("current_query", "")
    retry = state.get("retry_attempt", 0)

    # 检索去重：相同查询跳过（重试时会改写查询，所以 retry>0 时允许不同查询）
    last_query = state.get("last_search_query", "")
    if retry == 0 and query == last_query and last_query != "":
        logger.debug("检索去重：相同查询跳过，使用已有结果")
        return {
            "skip_search": True,
            "route": "generate",
            "tool_call_count": state.get("tool_call_count", 0),
        }

    # 重试时改写查询：去掉具体限定词，扩大召回
    if retry > 0:
        query = _broaden_query(query)

    top_k = DEFAULT_TOP_K
    hits = knowledge_search(query, top_k=top_k)

    tool_tracker = ToolCallTracker()
    tool_tracker.record("knowledge_search", {"query": query, "top_k": top_k}, hits)

    # V1 简化：过滤已过期文档 + 标记剩余结果
    doc_ids = [((h.get("metadata") or {}).get("document_id")) for h in hits if h.get("metadata")]
    doc_ids = [did for did in doc_ids if did is not None]

    db = SessionLocal()
    try:
        expired_ids = filter_expired_docs(db, doc_ids)
    finally:
        db.close()

    filtered_hits = [h for h in hits if (h.get("metadata") or {}).get("document_id") not in expired_ids]
    adjusted_hits = apply_temporal_adjustment(filtered_hits, expired_ids)

    return {
        "search_results": adjusted_hits,
        "last_search_query": query,
        "tool_call_count": tool_tracker.count,
        "confidence": adjusted_hits[0]["score"] if adjusted_hits else 0.0,
        "citations": build_citations(adjusted_hits),
        "route": "generate",
        "reasoning_chain": state.get("reasoning_chain", []) + [
            {
                "step": "search",
                "query": query,
                "hit_count": len(adjusted_hits),
                "top_score": adjusted_hits[0]["score"] if adjusted_hits else 0.0,
                "expired_count": len(expired_ids),
            }
        ],
    }


def _broaden_query(query: str) -> str:
    """重试时去掉限定词，扩大检索范围。"""
    # 去掉常见限定词
    stop_words = ["具体", "详细", "最新", "今年", "2024", "2025", "怎么", "如何", "什么"]
    broadened = query
    for sw in stop_words:
        broadened = broadened.replace(sw, "")
    # 清理多余空格
    broadened = " ".join(broadened.split())
    return broadened if broadened else query


# ==================== 置信度检查节点（带动态降级）====================


def check_confidence(state: dict) -> dict:
    """动态置信度判断：决定接受/重试/拒答。

    防条件判断循环：每次重试自动降低阈值，最多重试 3 次。
    """
    query = state.get("current_query", "")
    confidence = state.get("confidence", 0.0)
    hits = state.get("search_results", [])
    citations = state.get("citations", [])
    retry = state.get("retry_attempt", 0)

    accepted, reason = threshold_checker.should_accept_result(
        query=query,
        confidence=confidence,
        results_count=len(hits),
        has_citation=bool(citations),
        retry_attempt=retry,
    )

    if accepted:
        return {
            "should_refuse": False,
            "should_retry": False,
            "retry_attempt": retry,
            "reasoning_chain": state.get("reasoning_chain", []) + [
                {"step": "confidence_check", "accepted": True, "confidence": confidence, "reason": reason},
            ],
        }

    # 不通过，判断是否还有重试机会
    if threshold_checker.should_retry(retry):
        logger.info("置信度不足(%.2f)，第%d次重试: %s", confidence, retry + 1, reason)
        return {
            "should_refuse": False,
            "should_retry": True,
            "retry_attempt": retry + 1,
            "reasoning_chain": state.get("reasoning_chain", []) + [
                {
                    "step": "confidence_check",
                    "accepted": False,
                    "confidence": confidence,
                    "reason": reason,
                    "action": "retry",
                    "retry_attempt": retry + 1,
                }
            ],
        }

    # 重试耗尽 → 降级回答（带警告），不拒答
    logger.warning("置信度重试耗尽(retry=%d)，降级回答", retry)
    return {
        "should_refuse": False,
        "should_retry": False,
        "is_low_confidence": True,
        "retry_attempt": retry + 1,
        "reasoning_chain": state.get("reasoning_chain", []) + [
            {
                "step": "confidence_check",
                "accepted": False,
                "confidence": confidence,
                "reason": reason,
                "action": "degrade",
            }
        ],
    }


# ==================== 回答生成节点 ====================


def generate_response(state: dict) -> dict:
    """带引用生成回答。"""
    query = state.get("current_query", "")
    hits = state.get("search_results", [])
    is_low_confidence = state.get("is_low_confidence", False)

    if not hits:
        return _refuse(state, "未检索到相关就业资料，无法回答该问题。")

    # 组装参考资料
    blocks = []
    for i, h in enumerate(hits, start=1):
        src = h.get("document_title") or "未知来源"
        page = f" 第{h['page_no']}页" if h.get("page_no") else ""
        blocks.append(f"[{i}] 来源：《{src}》{page}\n{h.get('content', '')}")
    context = "\n\n".join(blocks)

    user_content = GENERATOR_USER_PROMPT.format(context=context, query=query)

    try:
        response, usage = chat_with_usage(
            [
                {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=DEFAULT_TEMPERATURE,
        )
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
    except Exception as e:
        logger.error("LLM 生成失败: %s", str(e))
        return _refuse(state, f"生成回答时遇到问题，请稍后再试或联系就业中心老师。")

    return {
        "response": response,
        "is_low_confidence": is_low_confidence,
        "llm_tokens_in": prompt_tokens,
        "llm_tokens_out": completion_tokens,
        "reasoning_chain": state.get("reasoning_chain", []) + [
            {"step": "generate", "response_length": len(response)},
        ],
    }


# ==================== 重新生成节点（带修正提示）====================


def regenerate_with_hints(state: dict) -> dict:
    """带修正提示的重新生成。

    防结果验证循环：只对 high 严重度问题注入修正信息。
    """
    query = state.get("current_query", "")
    hits = state.get("search_results", [])
    issues = state.get("consistency_issues", [])

    if not hits:
        return _refuse(state, "检索结果为空，无法重新生成。")

    blocks = []
    for i, h in enumerate(hits, start=1):
        src = h.get("document_title") or "未知来源"
        page = f" 第{h['page_no']}页" if h.get("page_no") else ""
        blocks.append(f"[{i}] 来源：《{src}》{page}\n{h.get('content', '')}")
    context = "\n\n".join(blocks)

    # 构造修正提示（只取 high 严重度）
    hints = []
    for issue in issues:
        if issue.get("severity") == "high":
            hints.append(
                f"- 注意：关于'{issue.get('contradiction_type', '')}'，之前回答与此矛盾，请修正。"
            )
    hints_text = "\n".join(hints) if hints else "无特定修正提示，请确保回答准确。"

    user_content = REGENERATOR_USER_PROMPT.format(
        context=context,
        query=query,
        hints=hints_text,
    )

    try:
        response, usage = chat_with_usage(
            [
                {"role": "system", "content": REGENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=DEFAULT_TEMPERATURE,
        )
        completion_tokens = usage.get("completion_tokens", 0)
    except Exception as e:
        logger.error("LLM 重新生成失败: %s", str(e))
        return _refuse(state, "重新生成回答时遇到问题，请稍后再试。")

    return {
        "response": response,
        "regenerate_count": state.get("regenerate_count", 0) + 1,
        "llm_tokens_out": completion_tokens,
        "reasoning_chain": state.get("reasoning_chain", []) + [
            {"step": "regenerate", "regenerate_count": state.get("regenerate_count", 0) + 1},
        ],
    }


# ==================== 一致性检查节点 ====================


def check_consistency(state: dict) -> dict:
    """自我一致性检查。

    V1 简化：只做轻量标记，不做多轮生成比对。
    防结果验证循环：验证器降级，不阻塞流程。
    """
    response = state.get("response", "")
    history = state.get("history", [])

    try:
        is_consistent, issues = consistency_checker.check(response, history)
    except Exception as e:
        # 验证器降级：非阻塞
        logger.warning("一致性检查异常，跳过: %s", str(e))
        return {
            "is_consistent": True,
            "consistency_issues": [],
            "skipped_consistency_check": True,
            "reasoning_chain": state.get("reasoning_chain", []) + [
                {"step": "consistency_check", "skipped": True, "reason": str(e)},
            ],
        }

    high_count = sum(1 for i in issues if i.get("severity") == "high")
    medium_count = sum(1 for i in issues if i.get("severity") == "medium")

    return {
        "is_consistent": is_consistent,
        "consistency_issues": issues,
        "high_severity_count": high_count,
        "medium_severity_count": medium_count,
        "reasoning_chain": state.get("reasoning_chain", []) + [
            {
                "step": "consistency_check",
                "is_consistent": is_consistent,
                "high_count": high_count,
                "medium_count": medium_count,
            }
        ],
    }


# ==================== 事实核验节点 ====================


def verify_facts(state: dict) -> dict:
    """事实核验：正则验证政策编号、日期、金额等。"""
    response = state.get("response", "")

    issues = fact_verifier.verify(response)

    return {
        "fact_issues": issues,
        "reasoning_chain": state.get("reasoning_chain", []) + [
            {"step": "fact_verification", "issue_count": len(issues)},
        ],
    }


# ==================== 内容审核节点 ====================


def content_moderation(state: dict) -> dict:
    """LLM 输出内容审核：检查是否包含违规内容。

    与输入侧敏感词过滤形成双重防护。
    """
    import re

    response = state.get("response", "")

    # V1 简化：只做关键词匹配，不额外调 LLM（成本考虑）
    sensitive_patterns = {
        "politics": ["国家领导人", "主席", "总理", "反动", "颠覆"],
        "contact": [r"\d{3}-\d{8}", r"\d{11}"],
        "ad": ["加我微信", "私信", "代做", "枪手", "收费"],
    }

    violations = []
    for category, patterns in sensitive_patterns.items():
        for pattern in patterns:
            if pattern.startswith("\\") or any(c in pattern for c in ["*", "+", "?", "[", "]", "(", ")", "{", "}", "|", "^", "$"]):
                # 正则匹配
                if re.search(pattern, response):
                    violations.append(category)
                    break
            else:
                # 字面匹配
                if pattern in response:
                    violations.append(category)
                    break

    if violations:
        logger.warning("内容审核发现违规: %s", violations)
        return {
            "should_refuse": True,
            "refusal_reason": "回答内容包含违规信息，已拦截。",
            "content_safe": False,
            "content_violations": list(set(violations)),
        }

    return {"content_safe": True}


# ==================== 拒答节点 ====================


def generate_refusal(state: dict) -> dict:
    """生成拒答回复（V1 简化版：直接返回模板，不调 LLM）。"""
    reason = state.get("refusal_reason", "无法回答该问题。")
    query = state.get("current_query", "")

    # V1 简化：直接返回模板，不调 LLM（节省成本 + 降低延迟）
    response = get_refusal_response(reason=reason, question=query)

    return {
        "response": response,
        "should_refuse": True,
        "is_no_answer": True,
    }


def direct_response(state: dict) -> dict:
    """简单问候的直接回复（不走检索）。"""
    query = state.get("current_query", "")
    response = f"你好！我是就业服务助手，有什么可以帮助你的吗？"
    return {
        "response": response,
        "route": "direct",
        "confidence": 1.0,
        "is_no_answer": False,
    }


# ==================== 接受但附加警告 ====================


def accept_with_warning(state: dict) -> dict:
    """接受回答但附加警告（低置信度 / 中等严重度问题）。"""
    warnings = []

    if state.get("is_low_confidence"):
        warnings.append("⚠️ 该回答基于有限资料，仅供参考，建议您咨询就业中心老师确认。")

    medium_issues = [i for i in state.get("consistency_issues", []) if i.get("severity") == "medium"]
    if medium_issues:
        warnings.append("⚠️ 回答中部分内容可能存在不一致，请以官方文件为准。")

    temporal_warnings = state.get("temporal_warnings", [])
    warnings.extend(temporal_warnings)

    return {
        "response": state.get("response", ""),
        "warnings": warnings,
        "should_refuse": False,
        "is_low_confidence": state.get("is_low_confidence", False),
    }


# ==================== 错误处理节点 ====================


def error_handler(state: dict) -> dict:
    """统一错误处理：记录错误，返回友好提示。"""
    error = state.get("error")
    if not error:
        return state

    request_id = state.get("request_id", "")
    logger.error(
        "请求 %s 处理异常: %s | %s",
        request_id,
        error.get("type", "unknown"),
        error.get("message", ""),
    )

    return {
        "response": "抱歉，系统处理您的请求时遇到了问题，请稍后再试或联系就业中心老师。",
        "should_refuse": True,
        "is_error": True,
        "error": error,
    }


# ==================== 内部辅助函数 ====================


def _refuse(state: dict, reason: str) -> dict:
    """内部方法：返回拒答状态。"""
    return {
        "should_refuse": True,
        "refusal_reason": reason,
        "response": "",
        "reasoning_chain": state.get("reasoning_chain", []) + [
            {"step": "refuse", "reason": reason},
        ],
    }
