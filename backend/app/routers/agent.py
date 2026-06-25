"""Agent 对话路由：同步接口（渐进式迁移开关）。"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime
from threading import Lock
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.agent.graph import get_agent_graph
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models import QaConversation, QaMessage, QaMessageReference, SysUser
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.utils.conversation import resolve_conversation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Agent对话"])


# ==================== Agent 专属限流 ====================


class _RateLimiter:
    """简单内存限流器：每用户 + 全局，基于滑动窗口计数。"""

    def __init__(self) -> None:
        self._user_windows: dict[int, list[float]] = defaultdict(list)
        self._global_window: list[float] = []
        self._lock = Lock()

    def check(self, user_id: int, per_user_limit: int, global_limit: int, window: int = 60) -> None:
        """检查是否超限，超限抛 HTTPException。"""
        now = time.time()
        cutoff = now - window

        with self._lock:
            self._global_window = [t for t in self._global_window if t > cutoff]
            self._user_windows[user_id] = [t for t in self._user_windows[user_id] if t > cutoff]

            if len(self._global_window) >= global_limit:
                logger.warning("全局限流触发：%d 次/%d秒", len(self._global_window), window)
                raise HTTPException(status_code=429, detail="当前咨询量较大，请稍候再试")

            if len(self._user_windows[user_id]) >= per_user_limit:
                logger.warning(
                    "用户限流触发：user_id=%d, %d 次/%d秒",
                    user_id,
                    len(self._user_windows[user_id]),
                    window,
                )
                raise HTTPException(status_code=429, detail="您提问过于频繁，请稍后再试")

            self._global_window.append(now)
            self._user_windows[user_id].append(now)


_rate_limiter = _RateLimiter()


# ==================== 内部辅助 ====================


def _save_agent_messages(
    db: Session,
    conv: QaConversation,
    query: str,
    result: dict[str, Any],
    user_id: int,
) -> QaMessage:
    """保存用户提问 + AI 回答消息（含引用）。"""
    db.add(QaMessage(conversation_id=conv.id, role=1, content=query))

    answer = result.get("response", "")
    is_no_answer = result.get("is_no_answer", False)
    answer_type = 4 if is_no_answer else 1

    msg = QaMessage(
        conversation_id=conv.id,
        role=2,
        content=answer,
        answer_type=answer_type,
        is_no_answer=1 if is_no_answer else 0,
        llm_model="agent-workflow",
        latency_ms=0,
        confidence=result.get("confidence"),
        query_risk_level=result.get("query_risk_level"),
        consistency_issues=str(result.get("consistency_issues", [])),
        fact_issues=str(result.get("fact_issues", [])),
        temporal_warnings=str(result.get("temporal_warnings", [])),
        prompt_tokens=result.get("llm_tokens_in") or 0,
        completion_tokens=result.get("llm_tokens_out") or 0,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    if not is_no_answer:
        for rank, cit in enumerate(result.get("citations", []), start=1):
            db.add(
                QaMessageReference(
                    message_id=msg.id,
                    document_id=cit.get("document_id"),
                    chunk_id=cit.get("chunk_id"),
                    score=cit.get("score"),
                    rank_no=rank,
                    snippet=(cit.get("snippet") or "")[:300],
                )
            )
    db.commit()
    return msg


async def _run_agent(query: str, user_id: int, conversation_id: int | None, db: Session) -> tuple[dict[str, Any], QaConversation]:
    """执行 Agent 工作流，返回 (结果字典, 会话对象)。"""
    from app.core.config import settings
    from app.core.semantic_cache import semantic_cache

    # 语义缓存：只对简单检索类查询做缓存（不走 Agent 工作流）
    # Agent 多步推理结果暂不缓存（V2 再做）
    cached = None
    if settings.semantic_cache_enabled:
        try:
            cached = await semantic_cache.get(query)
        except Exception as e:
            logger.debug("语义缓存查询跳过: %s", str(e))

    if cached:
        logger.info("语义缓存命中: query='%s', type=%s", query[:50], cached.get("cache_type"))
        conv = resolve_conversation(db, user_id, conversation_id, query)
        result = {
            "conversation_id": conv.id,
            "response": cached["response"],
            "confidence": cached.get("confidence", 0.95),
            "is_no_answer": False,
            "route": "cached",
            "citations": [],
            "consistency_issues": [],
            "fact_issues": [],
            "temporal_warnings": [],
            "warnings": ["💡 这是根据您之前问过的相似问题返回的参考回答，如有疑问建议咨询就业中心老师。"],
            "query_risk_level": "low",
            "is_low_confidence": False,
            "is_error": False,
            "request_id": str(uuid.uuid4()),
        }
        return result, conv

    _rate_limiter.check(
        user_id,
        per_user_limit=settings.agent_rate_limit_per_user,
        global_limit=settings.agent_rate_limit_global,
    )

    conv = resolve_conversation(db, user_id, conversation_id, query)

    state: dict[str, Any] = {
        "messages": [],
        "current_query": query,
        "conversation_id": conv.id,
        "user_id": user_id,
        "request_id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
        "retry_attempt": 0,
        "tool_call_count": 0,
        "regenerate_count": 0,
        "forced_exit": False,
        "is_low_confidence": False,
        "skipped_consistency_check": False,
        "is_error": False,
        "should_refuse": False,
        "refusal_reason": "",
        "content_safe": True,
        "search_results": [],
        "citations": [],
        "confidence": 0.0,
        "query_risk_level": "medium",
        "route": "",
        "response": "",
        "consistency_issues": [],
        "fact_issues": [],
        "temporal_warnings": [],
        "history": [],
        "reasoning_chain": [],
        "error": {},
        "partial_effects": [],
        "last_search_query": "",
        "llm_tokens_in": 0,
        "llm_tokens_out": 0,
        "warnings": [],
    }

    workflow = get_agent_graph().build()
    app = workflow.compile()

    config = {"configurable": {"thread_id": str(conv.id)}}
    try:
        result = await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(None, app.invoke, state, config),
            timeout=settings.agent_timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.error(
            "Agent 工作流超时：user=%d conv=%d timeout=%ds",
            user_id,
            conv.id,
            settings.agent_timeout_seconds,
        )
        result = {
            "response": "抱歉，系统处理您的请求时遇到了超时，请稍后再试或联系就业中心老师。",
            "confidence": 0.0,
            "should_refuse": True,
            "route": "error",
            "citations": [],
            "consistency_issues": [],
            "fact_issues": [],
            "temporal_warnings": [],
            "warnings": ["系统响应超时，请稍后再试。"],
            "query_risk_level": "medium",
            "is_low_confidence": True,
            "is_error": True,
        }

    output: dict[str, Any] = {
        "conversation_id": conv.id,
        "response": result.get("response", ""),
        "confidence": result.get("confidence", 0.0),
        "is_no_answer": result.get("should_refuse", False),
        "route": result.get("route", ""),
        "citations": result.get("citations", []),
        "consistency_issues": result.get("consistency_issues", []),
        "fact_issues": result.get("fact_issues", []),
        "temporal_warnings": result.get("temporal_warnings", []),
        "warnings": result.get("warnings", []),
        "query_risk_level": result.get("query_risk_level", "medium"),
        "is_low_confidence": result.get("is_low_confidence", False),
        "is_error": result.get("is_error", False),
        "request_id": state["request_id"],
        "llm_tokens_in": result.get("llm_tokens_in", 0),
        "llm_tokens_out": result.get("llm_tokens_out", 0),
    }
    return output, conv


# ==================== 端点 ====================


@router.post("/chat", summary="Agent 同步对话")
async def agent_chat(
    payload: AgentChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    current: SysUser = Depends(get_current_user),
) -> dict:
    """Agent 同步对话接口。

    渐进式迁移：agent_enabled=False 时切回旧 RAG。
    """
    from app.core.config import settings

    if not settings.agent_enabled:
        from app.services import rag_service

        result = rag_service.ask(db, current.id, payload.query, payload.conversation_id)
        return success(result)

    start = datetime.now()
    result, conv = await _run_agent(payload.query, current.id, payload.conversation_id, db)

    msg = _save_agent_messages(db, conv, payload.query, result, current.id)
    result["message_id"] = msg.id

    latency = int((datetime.now() - start).total_seconds() * 1000)
    logger.info(
        "Agent chat完成：user=%d conv=%d latency=%dms route=%s",
        current.id,
        result["conversation_id"],
        latency,
        result["route"],
    )

    resp = AgentChatResponse(**result)
    return success(resp.model_dump())


# TODO: V2 再做流式 Agent 响应
# @router.post("/chat/stream", summary="Agent 流式对话（V2 支持）")
# async def agent_chat_stream(...):
#     pass
