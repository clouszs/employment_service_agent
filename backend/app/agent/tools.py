"""Agent 工具集：当前阶段只需知识库检索，后续扩展。"""

from __future__ import annotations

from typing import Any

from app.core.llm import chat


# ==================== 检索工具 ====================


def knowledge_search(
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """知识库语义检索。

    返回命中片段列表，每条包含 document_title / content / score / page_no。
    无结果时返回空列表。
    """
    from app.services.rag_service import search as rag_search
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        return rag_search(db, query, top_k=top_k)
    finally:
        db.close()


# ==================== 工具注册表 ====================

TOOLS: dict[str, Any] = {
    "knowledge_search": knowledge_search,
}

# ==================== 工具调用记录 ====================


class ToolCallTracker:
    """工具调用计数器 + 调用记录。"""

    def __init__(self) -> None:
        self.count: int = 0
        self.calls: list[dict] = []

    def record(self, tool_name: str, args: dict, result: Any) -> None:
        self.count += 1
        self.calls.append(
            {
                "tool": tool_name,
                "args": args,
                "result_summary": str(result)[:200] if result else None,
            }
        )

    def should_stop(self, max_calls: int = 3) -> bool:
        return self.count >= max_calls
