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
from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentGraph:
    """LangGraph Agent 工作流构建器。"""

    def __init__(self) -> None:
        self.graph: StateGraph | None = None

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

        # regenerate → generate（后续可扩展为跳转回 search）
        graph.add_edge("regenerate", "generate")

        # generate → check_consistency → verify_facts → content_moderation
        graph.add_edge("generate", "check_consistency")
        graph.add_edge("check_consistency", "verify_facts")
        graph.add_edge("verify_facts", "content_moderation")

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
        """编译工作流，配置 Checkpoint。"""
        graph = self.build()
        checkpointer = SqliteSaver(db_path=db_path)

        compiled = graph.compile(checkpointer)
        logger.info(
            "AgentGraph 已编译：checkpointer=%s",
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


# ==================== 全局单例 ====================


_agent_graph: AgentGraph | None = None


def get_agent_graph() -> AgentGraph:
    """获取 AgentGraph 单例。"""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = AgentGraph()
    return _agent_graph
