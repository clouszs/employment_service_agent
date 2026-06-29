"""职位推荐服务（学生自助）。

V1：复用知识库 RAG 检索，从职位类文档中匹配，返回标准化职位列表。
确定性检索，不调用 LLM，也不经过 Agent 工作流（用户主动触发的查询）。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services import rag_service

logger = logging.getLogger(__name__)


def recommend_jobs(
    db: Session,
    query: str,
    top_k: int = 5,
    location: Optional[str] = None,
) -> list[dict[str, Any]]:
    """基于知识库检索推荐职位。

    Args:
        db: 数据库会话
        query: 关键词/岗位方向
        top_k: 返回条数
        location: 可选地点过滤（对片段做关键词包含过滤）

    Returns:
        职位列表，每项含 title/score/source/snippet/document_id。
    """
    q = (query or "").strip()
    if not q:
        return []

    try:
        hits = rag_service.search(db, q, top_k=max(1, top_k))
    except Exception as exc:  # noqa: BLE001
        logger.warning("recommend_jobs 检索失败: query=%s err=%s", q, exc)
        return []

    jobs: list[dict[str, Any]] = []
    for hit in hits:
        snippet = (hit.get("content") or "").strip()
        if location and location not in snippet:
            continue
        jobs.append(
            {
                "title": hit.get("document_title") or "未命名职位",
                "score": float(hit.get("score") or 0.0),
                "source": "knowledge_base",
                "snippet": snippet[:200],
                "document_id": hit.get("document_id"),
            }
        )
    return jobs
