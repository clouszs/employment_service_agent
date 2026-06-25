"""引用质量评估监控：V1 简化版。

复用 `citation_tracker.evaluate_citation_quality()` 的评估逻辑，
增加写入 `CitationQualityLog` 的能力，供监控/定时任务调用。
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.agent.citation_tracker import evaluate_citation_quality
from app.models import CitationQualityLog

logger = logging.getLogger(__name__)


class CitationQualityEvaluator:
    """引用质量评估器（V1 简化版）。"""

    def evaluate_and_log(
        self,
        db: Session,
        message_id: int,
        citations: list[dict],
    ) -> dict[str, Any]:
        """评估引用质量并写入日志。

        Args:
            db: 数据库会话
            message_id: 对应回答消息 ID
            citations: 引用列表

        Returns:
            评估结果字典
        """
        result = evaluate_citation_quality(citations)

        try:
            log = CitationQualityLog(
                message_id=message_id,
                total_sentences=len(citations),
                direct_count=result.get("direct_count", 0),
                indirect_count=result.get("indirect_count", 0),
                none_count=result.get("none_count", 0),
                avg_confidence=result.get("avg_score"),
                quality_score=result.get("quality_score"),
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.warning("写入 citation_quality_log 失败: %s", str(e))
            db.rollback()

        return result
