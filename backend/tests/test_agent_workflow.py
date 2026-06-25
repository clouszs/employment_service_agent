"""Agent 工作流单元测试：路由、检索、置信度、生成、拒答。"""

from __future__ import annotations

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def test_route_query():
    """测试路由决策。"""
    from app.agent.nodes import route_query

    # 低风险问候
    state = {"current_query": "你好", "tool_call_count": 0}
    result = route_query(state)
    assert result["route"] == "direct", f"Expected direct, got {result['route']}"
    assert result["query_risk_level"] == "low"
    logger.info("✅ 低风险问候路由正确")

    # 高风险政策查询
    state = {"current_query": "落户政策有哪些", "tool_call_count": 0}
    result = route_query(state)
    assert result["route"] == "search", f"Expected search, got {result['route']}"
    assert result["query_risk_level"] == "high"
    logger.info("✅ 高风险政策查询路由正确")

    # 工具选择循环防护
    state = {"current_query": "落户政策", "tool_call_count": 3}
    result = route_query(state)
    assert result["route"] == "generate", f"Expected generate, got {result['route']}"
    assert result["forced_exit"] is True
    logger.info("✅ 工具选择循环防护正确")


def test_search_knowledge_dedup():
    """测试检索去重。"""
    from app.agent.nodes import search_knowledge

    # 相同查询应该去重
    state = {
        "current_query": "测试查询",
        "last_search_query": "测试查询",
        "retry_attempt": 0,
    }
    result = search_knowledge(state)
    assert result.get("skip_search") is True, "相同查询应该被去重"
    assert result["route"] == "generate"
    logger.info("✅ 检索去重正确")

    # 不同查询应该检索
    state = {
        "current_query": "新查询",
        "last_search_query": "旧查询",
        "retry_attempt": 0,
    }
    result = search_knowledge(state)
    assert result.get("skip_search") is not True
    logger.info("✅ 不同查询正常检索")


def test_dynamic_threshold():
    """测试动态置信度阈值。"""
    from app.agent.hallucination_defense import threshold_checker

    # 首次检查：高风险，置信度 0.69 < 0.80，不通过
    accepted, reason = threshold_checker.should_accept_result(
        query="落户政策", confidence=0.69, results_count=3, has_citation=True, retry_attempt=0
    )
    assert not accepted, "首次高风险 0.69 应该不通过"
    logger.info(f"✅ 首次高风险阈值正确: {reason}")

    # 第二次重试：阈值降至 0.65，0.69 >= 0.65，通过
    accepted, reason = threshold_checker.should_accept_result(
        query="落户政策", confidence=0.69, results_count=3, has_citation=True, retry_attempt=1
    )
    assert accepted, "第二次高风险 0.69 应该通过（阈值降至 0.65）"
    logger.info(f"✅ 第二次重试阈值正确: {reason}")

    # 连续重试到保底 0.30（用 low 风险查询，require_citation=False）
    for retry in range(4):
        accepted, reason = threshold_checker.should_accept_result(
            query="你好", confidence=0.35, results_count=1, has_citation=False, retry_attempt=retry
        )
    assert accepted, "第 3 次后阈值应降至 0.30，0.35 应通过"
    logger.info(f"✅ 保底阈值正确: retry={retry}, accepted={accepted}, reason={reason}")


def test_check_confidence_retry():
    """测试置信度检查节点的重试逻辑。"""
    from app.agent.nodes import check_confidence

    # 置信度不足，还有重试机会
    state = {
        "current_query": "落户政策",
        "confidence": 0.5,
        "search_results": [],
        "citations": [],
        "retry_attempt": 0,
    }
    result = check_confidence(state)
    assert result["should_retry"] is True
    assert result["retry_attempt"] == 1
    logger.info("✅ 置信度不足触发重试")

    # 重试耗尽，降级回答
    state["retry_attempt"] = 3
    result = check_confidence(state)
    assert result["should_retry"] is False
    assert result["is_low_confidence"] is True
    logger.info("✅ 重试耗尽降级回答")


def test_content_moderation():
    """测试内容审核节点。"""
    from app.agent.nodes import content_moderation

    # 正常内容
    state = {"response": "你好，有什么可以帮助你的吗？"}
    result = content_moderation(state)
    assert result["content_safe"] is True
    logger.info("✅ 正常内容审核通过")

    # 违规内容
    state = {"response": "加我微信，私信代做枪手"}
    result = content_moderation(state)
    assert result["content_safe"] is False
    assert result["should_refuse"] is True
    logger.info("✅ 违规内容审核拦截")


def test_error_handler():
    """测试错误处理节点。"""
    from app.agent.nodes import error_handler

    # 无错误
    state = {"error": {}}
    result = error_handler(state)
    assert result.get("is_error") is not True
    logger.info("✅ 无错误状态正常")

    # 有错误
    state = {"error": {"type": "LLMError", "message": "timeout"}}
    result = error_handler(state)
    assert result["is_error"] is True
    assert result["should_refuse"] is True
    assert "抱歉" in result["response"]
    logger.info("✅ 错误处理返回友好提示")


if __name__ == "__main__":
    test_route_query()
    test_search_knowledge_dedup()
    test_dynamic_threshold()
    test_check_confidence_retry()
    test_content_moderation()
    test_error_handler()
    logger.info("所有单元测试通过！")
