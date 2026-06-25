"""引用追踪：V1 简化版（chunk 级别引用 + 质量评估）。

V2 升级路径：句子级别引用 + LLM 验证支持度（direct/indirect/none）。
"""

from __future__ import annotations

import logging
from typing import Any

from app.agent.constants import CITATION_SNIPPET_MAX_LENGTH

logger = logging.getLogger(__name__)


# ===== V1：Chunk 级别引用（当前实现）=====


def build_citations(hits: list[dict]) -> list[dict]:
    """从检索结果构建引用列表（V1 简化：chunk 级别）。

    Args:
        hits: 检索结果列表（来自 rag_service.search）

    Returns:
        引用列表，每条包含 rank / document_id / document_title / chunk_id /
        score / page_no / snippet
    """
    citations = []
    for rank, h in enumerate(hits, start=1):
        citations.append(
            {
                "rank": rank,
                "document_id": h.get("document_id"),
                "document_title": h.get("document_title"),
                "chunk_id": h.get("chunk_id"),
                "score": h.get("score"),
                "page_no": h.get("page_no"),
                "snippet": (h.get("content") or "")[:CITATION_SNIPPET_MAX_LENGTH],
            }
        )
    return citations


# ===== V1：引用质量评估（简化版）=====


def evaluate_citation_quality(citations: list[dict]) -> dict[str, Any]:
    """评估引用整体质量（V1 简化版）。

    V1 仅基于检索得分和引用数量做统计，不做 LLM 级验证。
    V2 再引入 SentenceLevelCitationTracker 做逐句验证。

    Args:
        citations: 引用列表

    Returns:
        质量评估结果
    """
    total = len(citations)
    if total == 0:
        return {
            "quality_score": 0.0,
            "direct_count": 0,
            "indirect_count": 0,
            "none_count": 0,
            "avg_score": 0.0,
            "issues": ["无引用"],
        }

    scores = [c.get("score") or 0.0 for c in citations]
    avg_score = sum(scores) / total

    # V1 简化：按得分区间映射为 direct / indirect / none
    direct_count = sum(1 for s in scores if s >= 0.75)
    indirect_count = sum(1 for s in scores if 0.40 <= s < 0.75)
    none_count = total - direct_count - indirect_count

    quality_score = (
        direct_count * 1.0 + indirect_count * 0.5 + none_count * 0.0
    ) / total

    issues = []
    if none_count > 0:
        issues.append(f"{none_count} 条引用得分较低")
    if avg_score < 0.5:
        issues.append(f"平均引用得分偏低({avg_score:.2f})")

    return {
        "quality_score": round(quality_score, 4),
        "direct_count": direct_count,
        "indirect_count": indirect_count,
        "none_count": none_count,
        "avg_score": round(avg_score, 4),
        "issues": issues,
    }


# ===== V2 预留接口（句子级别引用）=====


class SentenceLevelCitationTracker:
    """句子级别引用追踪器（V2 实现，V1 仅预留接口）。

    V2 实现要点：
    1. 将回答按 `。！？；` 切分为句子
    2. 对每个句子找最相关的来源 chunk（Embedding 相似度）
    3. 使用 LLM 验证引用支持度（direct / indirect / none）
    4. 返回句子级别引用列表
    """

    def __init__(self, embed_model: Any, llm_client: Any) -> None:
        self.embed_model = embed_model
        self.llm_client = llm_client

    def track(self, response: str, source_chunks: list[dict]) -> list[dict]:
        """追踪句子级别引用（V2 实现）。"""
        raise NotImplementedError("SentenceLevelCitationTracker.track() 将在 V2 实现")
