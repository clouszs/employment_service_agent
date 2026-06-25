"""时效感知检索：V1 简化版。

V1 仅基于现有 `KbDocument.effective_date` / `expire_date` 做降权，
不做完整时效性评分。V2 再扩展为综合得分排序。
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import KbDocument

logger = logging.getLogger(__name__)


# ===== V1：过期文档过滤 =====


def filter_expired_docs(db: Session, doc_ids: list[int]) -> set[int]:
    """过滤已过期文档 ID（V1 简化版）。

    仅检查 `KbDocument.expire_date`，已过期且未设为长期有效的文档会被过滤。

    Args:
        db: 数据库会话
        doc_ids: 候选文档 ID 列表

    Returns:
        已过期文档 ID 集合
    """
    if not doc_ids:
        return set()

    today = date.today()
    expired_rows = (
        db.query(KbDocument.id)
        .filter(
            KbDocument.id.in_(doc_ids),
            KbDocument.status == 1,
            KbDocument.expire_date.isnot(None),
            KbDocument.expire_date < today,
        )
        .all()
    )
    return {row.id for row in expired_rows}


def get_expiring_soon_docs(db: Session, warning_days: int = 30) -> list[dict]:
    """获取即将过期文档（V1 简化版，供监控模块调用）。

    Args:
        db: 数据库会话
        warning_days: 预警天数（默认 30 天）

    Returns:
        即将过期文档列表
    """
    today = date.today()
    warning_date = today + __import__("datetime").timedelta(days=warning_days)

    rows = (
        db.query(KbDocument)
        .filter(
            KbDocument.status == 1,
            KbDocument.expire_date.isnot(None),
            KbDocument.expire_date >= today,
            KbDocument.expire_date <= warning_date,
        )
        .order_by(KbDocument.expire_date.asc())
        .all()
    )

    return [
        {
            "id": row.id,
            "title": row.title,
            "expire_date": row.expire_date.isoformat() if row.expire_date else None,
            "days_until_expiry": (row.expire_date - today).days if row.expire_date else None,
        }
        for row in rows
    ]


# ===== V1：检索结果降权标记 =====


def apply_temporal_adjustment(hits: list[dict], expired_ids: set[int]) -> list[dict]:
    """对检索结果应用时效性调整（V1 简化：仅标记过期）。

    V1 不修改得分，仅对过期文档添加 `is_expired` 标记，
    由上层节点决定是否降权或展示警告。

    Args:
        hits: 检索结果列表
        expired_ids: 已过期文档 ID 集合

    Returns:
        调整后的检索结果列表
    """
    adjusted = []
    for h in hits:
        doc_id = (h.get("metadata") or {}).get("document_id")
        h_copy = dict(h)
        h_copy["is_expired"] = doc_id in expired_ids if doc_id is not None else False
        adjusted.append(h_copy)
    return adjusted


# ===== V2 预留接口（完整时效感知检索）=====


class TemporalAwareRetriever:
    """时效感知检索器（V2 实现，V1 仅预留接口）。

    V2 实现要点：
    1. 基础向量检索（取 top_k × 2 候选）
    2. 计算时效性得分（指数衰减：exp(-0.693 × days / half_life)）
    3. 综合得分 = 相似度 × 0.7 + 时效性 × 0.3
    4. 过期文档降权 × 0.1
    5. 按综合得分排序取 top_k
    """

    def __init__(self, base_retriever: Any, config: dict | None = None) -> None:
        self.base_retriever = base_retriever
        self.config = config or {
            "half_life_days": settings.kb_freshness_half_life,
            "similarity_weight": 0.7,
            "temporal_weight": 0.3,
            "expired_penalty": 0.1,
        }

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """时效感知检索（V2 实现）。"""
        raise NotImplementedError("TemporalAwareRetriever.retrieve() 将在 V2 实现")
