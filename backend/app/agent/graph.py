"""Agent 工作流图：LangGraph StateGraph 构建 + 编译。"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.sqlite_checkpoint import SqliteSaver
from app.agent.nodes import (
    accept_with_warning,
    check_confidence,
    check_consistency,
    content_moderation,
    direct_response,
    error_handler,
    generate_refusal,
    generate_response,
    regenerate_with_hints,
    route_query,
    search_knowledge,
    verify_facts,
)
from app.agent.state import AgentState
from app.agent.constants import MAX_REGENERATE_RETRY  # [Self-Refinement] 自校正熔断上限
from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentGraph:
    """LangGraph Agent 工作流构建器。"""

    def __init__(self) -> None:
        self.graph: StateGraph | None = None
        self._compiled_graph: Any | None = None

    def build(self) -> StateGraph:
        """构建工作流图（节点 + 边）。"""
        graph = StateGraph(AgentState)

        # ===== 注册节点 =====
        graph.add_node("route", route_query)
        graph.add_node("search", search_knowledge)
        graph.add_node("check_confidence", check_confidence)
        graph.add_node("generate", generate_response)
        graph.add_node("regenerate", regenerate_with_hints)
        graph.add_node("check_consistency", check_consistency)
        graph.add_node("verify_facts", verify_facts)
        graph.add_node("content_moderation", content_moderation)
        graph.add_node("accept_with_warning", accept_with_warning)
        graph.add_node("refuse", generate_refusal)
        graph.add_node("error_handler", error_handler)
        graph.add_node("direct_response", direct_response)

        # ===== 定义边 =====
        graph.add_edge(START, "route")

        # route 分支
        graph.add_conditional_edges(
            "route",
            _route_decision,
            {
                "search": "search",
                "direct": "direct_response",
                "refuse": "refuse",
            },
        )

        # search → check_confidence
        graph.add_edge("search", "check_confidence")

        # check_confidence 三分支
        graph.add_conditional_edges(
            "check_confidence",
            _confidence_decision,
            {
                "accept": "generate",
                "regenerate": "regenerate",
                "refuse": "refuse",
            },
        )

        # generate → check_consistency → verify_facts
        graph.add_edge("generate", "check_consistency")
        graph.add_edge("check_consistency", "verify_facts")

        # [Self-Refinement] 修改：verify_facts 之后改为条件边，进入三阶段自校正闭环
        graph.add_conditional_edges(
            "verify_facts",
            _verify_decision,
            {
                "accept": "content_moderation",
                "regenerate": "regenerate",
                "refuse": "refuse",
            },
        )

        # [Self-Refinement] 修改：regenerate 之后改为条件边，根据重试次数决定回到审查或熔断
        graph.add_conditional_edges(
            "regenerate",
            _after_regenerate_decision,
            {
                "verify_facts": "verify_facts",
                "content_moderation": "content_moderation",
            },
        )

        # content_moderation → 最终决策
        graph.add_conditional_edges(
            "content_moderation",
            _post_moderation_decision,
            {
                "accept": END,
                "accept_with_warning": "accept_with_warning",
                "refuse": "refuse",
            },
        )

        # accept_with_warning → error_handler → END
        graph.add_edge("accept_with_warning", "error_handler")
        graph.add_edge("refuse", "error_handler")
        graph.add_edge("error_handler", END)
        graph.add_edge("direct_response", END)

        self.graph = graph
        return graph

    def compile(self, db_path: str = "data/agent_checkpoints.db") -> Any:
        """编译工作流，配置 Checkpoint。

        第一次编译后缓存 compiled graph，后续直接返回缓存实例。
        """
        if self._compiled_graph is not None:
            logger.info("AgentGraph 使用已编译缓存")
            return self._compiled_graph

        graph = self.build()
        checkpointer = SqliteSaver(db_path=db_path)

        compiled = graph.compile(checkpointer)
        self._compiled_graph = compiled
        logger.info(
            "AgentGraph 已编译并缓存：checkpointer=%s",
            type(checkpointer).__name__,
        )
        return compiled


# ==================== 条件决策函数 ====================


def _route_decision(state: dict) -> str:
    """路由决策：根据 route 字段选择下一步。"""
    return state.get("route", "search")


def _confidence_decision(state: dict) -> str:
    """置信度决策：接受 / 重试 / 拒答。"""
    if state.get("should_refuse"):
        return "refuse"
    if state.get("should_retry"):
        return "regenerate"
    return "accept"


def _post_moderation_decision(state: dict) -> str:
    """内容审核后决策：接受 / 警告接受 / 拒答。"""
    if state.get("should_refuse"):
        return "refuse"
    if state.get("is_low_confidence") or state.get("warnings"):
        return "accept_with_warning"
    return "accept"


# [Self-Refinement] 新增：审查后决策（三阶段自校正闭环）
def _verify_decision(state: dict) -> str:
    """审查决策：根据事实核验结果决定 accept / regenerate / refuse。"""
    if state.get("should_refuse"):
        return "refuse"
    if state.get("should_retry"):
        return "regenerate"
    return "accept"


# [Self-Refinement] 新增：重生成后决策（熔断或回到审查环）
def _after_regenerate_decision(state: dict) -> str:
    """重生成后决策：未超限回到审查，超限熔断到内容审核。"""
    retry = state.get("retry_attempt", 0)
    if retry < MAX_REGENERATE_RETRY:
        return "verify_facts"
    logger.warning("重生成次数已达上限(%d)，熔断到内容审核", retry)
    return "content_moderation"


# ==================== 全局单例 ====================


_agent_graph: AgentGraph | None = None


def get_agent_graph() -> AgentGraph:
    """获取 AgentGraph 单例。"""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = AgentGraph()
    return _agent_graph
