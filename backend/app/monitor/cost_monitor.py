"""LLM 成本监控：按天/月统计调用量 + 成本，超阈值告警。

V1 简化版：
- 从已有的 `OpQueryLog` / `QaMessage` 统计成本
- 不接入 LangSmith API（避免额外依赖）
- 仅记录 + 日志告警，不做邮件/飞书推送
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import LlmCostLog, OpQueryLog, QaMessage

logger = logging.getLogger(__name__)


class LlmCostMonitor:
    """LLM 成本监控器（V1 简化版）。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run_daily_check(self, stat_date: date | None = None) -> dict[str, Any]:
        """执行一次成本统计。

        Args:
            stat_date: 统计日期（默认今天）

        Returns:
            成本报告字典
        """
        if stat_date is None:
            stat_date = date.today()

        # 1. 从 QaMessage 统计当天各模型的 token 消耗
        rows = (
            self.db.query(
                QaMessage.llm_model,
                func.count(QaMessage.id).label("call_count"),
                func.sum(QaMessage.prompt_tokens).label("tokens_in"),
                func.sum(QaMessage.completion_tokens).label("tokens_out"),
            )
            .filter(
                QaMessage.created_at >= stat_date,
                QaMessage.llm_model.isnot(None),
                QaMessage.llm_model != "",
            )
            .group_by(QaMessage.llm_model)
            .all()
        )

        report = {
            "stat_date": stat_date.isoformat(),
            "total_cost_usd": 0.0,
            "total_calls": 0,
            "models": [],
        }

        for row in rows:
            model = row.llm_model or "unknown"
            call_count = row.call_count or 0
            tokens_in = row.tokens_in or 0
            tokens_out = row.tokens_out or 0
            cost = self._estimate_cost(model, tokens_in, tokens_out)

            report["total_cost_usd"] += float(cost)
            report["total_calls"] += call_count
            report["models"].append({
                "model": model,
                "call_count": call_count,
                "tokens_in": int(tokens_in),
                "tokens_out": int(tokens_out),
                "cost_usd": round(float(cost), 4),
            })

            # 2. 写入 llm_cost_log
            self._upsert_cost_log(
                stat_date=stat_date,
                model=model,
                call_count=call_count,
                tokens_in=int(tokens_in),
                tokens_out=int(tokens_out),
                cost_usd=float(cost),
            )

        # 3. 阈值告警
        self._check_thresholds(report)

        logger.info(
            "LLM成本统计完成：date=%s, total_cost=%.4f USD, calls=%d",
            stat_date,
            report["total_cost_usd"],
            report["total_calls"],
        )

        return report

    def _estimate_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """估算成本（USD）。

        V1 简化：使用粗略单价，V2 可从配置/API 获取实时价格。
        """
        # 参考价格（$/1k tokens），实际应以 DashScope 定价为准
        price_map = {
            "qwen3.7-max": {"input": 0.002, "output": 0.006},
            "qwen-plus": {"input": 0.002, "output": 0.006},
            "qwen-turbo": {"input": 0.0003, "output": 0.0006},
            "text-embedding-v4": {"input": 0.0001, "output": 0.0},
        }

        prices = price_map.get(model, {"input": 0.002, "output": 0.006})

        cost_in = (tokens_in / 1000) * prices["input"]
        cost_out = (tokens_out / 1000) * prices["output"]

        return cost_in + cost_out

    def _upsert_cost_log(
        self,
        stat_date: date,
        model: str,
        call_count: int,
        tokens_in: int,
        tokens_out: int,
        cost_usd: float,
    ) -> None:
        """写入或更新 llm_cost_log。"""
        try:
            existing = self.db.scalar(
                select(LlmCostLog).where(
                    LlmCostLog.stat_date == stat_date,
                    LlmCostLog.model == model,
                )
            )

            if existing:
                existing.call_count = call_count
                existing.tokens_in = tokens_in
                existing.tokens_out = tokens_out
                existing.cost_usd = cost_usd
            else:
                self.db.add(
                    LlmCostLog(
                        stat_date=stat_date,
                        model=model,
                        call_count=call_count,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        cost_usd=cost_usd,
                    )
                )

            self.db.commit()
        except Exception as e:
            logger.warning("写入 llm_cost_log 失败: %s", str(e))
            self.db.rollback()

    def _check_thresholds(self, report: dict[str, Any]) -> None:
        """检查是否超阈值，触发日志告警。"""
        total_cost = report["total_cost_usd"]
        daily_threshold = settings.daily_cost_threshold_usd

        if total_cost >= daily_threshold:
            logger.warning(
                "LLM 日成本告警：%.4f USD >= %.4f USD (阈值)",
                total_cost,
                daily_threshold,
            )
            report.setdefault("alerts", []).append({
                "level": "warning",
                "message": f"日成本 {total_cost:.4f} USD 已达阈值 {daily_threshold} USD",
            })

    def get_monthly_cost(self, year: int, month: int) -> dict[str, Any]:
        """查询指定月份的成本统计。"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        rows = (
            self.db.query(
                LlmCostLog.model,
                func.sum(LlmCostLog.call_count).label("total_calls"),
                func.sum(LlmCostLog.tokens_in).label("total_tokens_in"),
                func.sum(LlmCostLog.tokens_out).label("total_tokens_out"),
                func.sum(LlmCostLog.cost_usd).label("total_cost"),
            )
            .filter(
                LlmCostLog.stat_date >= start_date,
                LlmCostLog.stat_date < end_date,
            )
            .group_by(LlmCostLog.model)
            .all()
        )

        total_cost = sum(float(row.total_cost or 0) for row in rows)

        return {
            "year": year,
            "month": month,
            "total_cost_usd": round(total_cost, 4),
            "models": [
                {
                    "model": row.model,
                    "call_count": int(row.total_calls or 0),
                    "tokens_in": int(row.total_tokens_in or 0),
                    "tokens_out": int(row.total_tokens_out or 0),
                    "cost_usd": round(float(row.total_cost or 0), 4),
                }
                for row in rows
            ],
        }
