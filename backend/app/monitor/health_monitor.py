"""知识库健康度监控：检查文档过期状态 + 计算健康度评分。"""

from __future__ import annotations

import logging
import math
from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import KbDocument, KbHealthLog

logger = logging.getLogger(__name__)


class KnowledgeBaseHealthMonitor:
    """知识库健康度监控器（V1 简化版）。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run_daily_check(self) -> dict[str, Any]:
        """执行一次健康检查，返回报告字典。"""
        today = date.today()

        # 1. 即将过期文档
        warning_date = today + __import__("datetime").timedelta(days=settings.kb_warning_days)
        warning_docs = self._query_docs_in_range(today, warning_date)

        # 2. 已过期文档
        expired_docs = self._query_expired_docs(today)

        # 3. 健康度评分
        health_score = self._calculate_health_score(today)

        report = {
            "check_date": today.isoformat(),
            "health_score": health_score,
            "warning_count": len(warning_docs),
            "expired_count": len(expired_docs),
            "warning_docs": warning_docs,
            "expired_docs": expired_docs,
        }

        # 4. 写入日志
        self._log_report(report)

        logger.info(
            "KB健康检查完成：score=%.2f, warning=%d, expired=%d",
            health_score,
            len(warning_docs),
            len(expired_docs),
        )

        return report

    def _query_docs_in_range(self, start: date, end: date) -> list[dict]:
        """查询在 [start, end] 区间内过期的文档。"""
        rows = (
            self.db.query(KbDocument)
            .filter(
                KbDocument.status == 1,
                KbDocument.expire_date.isnot(None),
                KbDocument.expire_date >= start,
                KbDocument.expire_date <= end,
            )
            .order_by(KbDocument.expire_date.asc())
            .all()
        )
        return [
            {
                "id": r.id,
                "title": r.title,
                "expire_date": r.expire_date.isoformat(),
                "days_until_expiry": (r.expire_date - start).days,
            }
            for r in rows
        ]

    def _query_expired_docs(self, today: date) -> list[dict]:
        """查询已过期文档。"""
        rows = (
            self.db.query(KbDocument)
            .filter(
                KbDocument.status == 1,
                KbDocument.expire_date.isnot(None),
                KbDocument.expire_date < today,
            )
            .order_by(KbDocument.expire_date.desc())
            .all()
        )
        return [
            {
                "id": r.id,
                "title": r.title,
                "expire_date": r.expire_date.isoformat(),
                "days_expired": (today - r.expire_date).days,
            }
            for r in rows
        ]

    def _calculate_health_score(self, today: date) -> float:
        """计算知识库整体健康度（0-100）。"""
        # 获取所有有效文档的有效期信息
        rows = (
            self.db.query(
                KbDocument.expire_date,
                KbDocument.effective_date,
            )
            .filter(
                KbDocument.status == 1,
                KbDocument.expire_date.isnot(None),
            )
            .all()
        )

        if not rows:
            return 100.0

        total_score = 0.0
        total_weight = 0.0

        half_life = settings.kb_freshness_half_life

        for row in rows:
            effective = row.effective_date or today
            expire = row.expire_date

            days_since = (today - effective).days
            freshness = math.exp(-0.693 * days_since / half_life)

            if expire < today:
                freshness *= 0.1  # 过期惩罚

            total_score += freshness
            total_weight += 1.0

        score = (total_score / total_weight) * 100 if total_weight > 0 else 100.0
        return round(score, 2)

    def _log_report(self, report: dict[str, Any]) -> None:
        """写入健康度日志。"""
        try:
            log = KbHealthLog(
                check_date=date.fromisoformat(report["check_date"]),
                health_score=report["health_score"],
                warning_docs=len(report["warning_docs"]),
                expired_docs=len(report["expired_docs"]),
                total_docs=self._count_total_docs(),
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.warning("写入 kb_health_log 失败: %s", str(e))
            self.db.rollback()

    def _count_total_docs(self) -> int:
        """统计当前有效文档总数。"""
        return (
            self.db.query(KbDocument)
            .filter(KbDocument.status == 1)
            .count()
        )
