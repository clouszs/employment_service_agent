from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import and_

from app.core.database import SessionLocal
from app.models import ConsistencyIssueLog, QaMessage, QaMessageReference
from app.monitor.citation_evaluator import CitationQualityEvaluator
from app.monitor.cost_monitor import LlmCostMonitor
from app.monitor.health_monitor import KnowledgeBaseHealthMonitor

logger = logging.getLogger(__name__)

# 全局调度器单例
_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler | None:
    """获取调度器实例。"""
    return _scheduler


def setup_scheduler() -> None:
    """初始化定时任务。"""
    global _scheduler

    if _scheduler is not None:
        logger.info("调度器已初始化，跳过重复注册")
        return

    _scheduler = AsyncIOScheduler()

    # 每日凌晨 2 点：知识库健康检查
    _scheduler.add_job(
        _run_kb_health_check,
        trigger=CronTrigger(hour=2, minute=0),
        id="kb_health_check",
        name="知识库每日健康检查",
        replace_existing=True,
    )

    # 每日凌晨 2:15：引用质量评估
    _scheduler.add_job(
        _run_citation_quality_check,
        trigger=CronTrigger(hour=2, minute=15),
        id="citation_quality_check",
        name="引用质量每日评估",
        replace_existing=True,
    )

    # 每日凌晨 2:30：LLM 成本统计
    _scheduler.add_job(
        _run_llm_cost_check,
        trigger=CronTrigger(hour=2, minute=30),
        id="llm_cost_check",
        name="LLM 每日成本统计",
        replace_existing=True,
    )

    # 每日凌晨 2:45：一致性问题检查
    _scheduler.add_job(
        _run_consistency_check,
        trigger=CronTrigger(hour=2, minute=45),
        id="consistency_check",
        name="一致性问题每日检查",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        "定时任务调度器已启动：kb_health_check + citation_quality_check + llm_cost_check + consistency_check"
    )


def shutdown_scheduler() -> None:
    """关闭调度器。"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("定时任务调度器已关闭")


# ==================== 定时任务实现 ====================


def _run_kb_health_check() -> None:
    """执行知识库健康检查（独立 DB 会话）。"""
    db = SessionLocal()
    try:
        monitor = KnowledgeBaseHealthMonitor(db)
        report = monitor.run_daily_check()
        logger.info("定时任务[KB健康检查]完成：score=%.2f", report.get("health_score", 0))
    except Exception as e:
        logger.error("定时任务[KB健康检查]失败: %s", str(e))
    finally:
        db.close()


def _run_llm_cost_check() -> None:
    """执行 LLM 成本统计（独立 DB 会话）。"""
    db = SessionLocal()
    try:
        monitor = LlmCostMonitor(db)
        report = monitor.run_daily_check()
        logger.info("定时任务[LLM成本统计]完成：cost=%.4f USD", report.get("total_cost_usd", 0))
    except Exception as e:
        logger.error("定时任务[LLM成本统计]失败: %s", str(e))
    finally:
        db.close()


def _run_citation_quality_check() -> None:
    """批量评估近期引用的质量（独立 DB 会话）。"""
    db = SessionLocal()
    try:
        from datetime import datetime

        cutoff = datetime.now() - timedelta(hours=24)
        rows = (
            db.query(QaMessage)
            .join(QaMessageReference, QaMessage.id == QaMessageReference.message_id)
            .filter(
                and_(
                    QaMessage.role == 2,
                    QaMessage.answer_type == 1,
                    QaMessage.created_at >= cutoff,
                )
            )
            .distinct(QaMessage.id)
            .all()
        )
        evaluated = 0
        for msg in rows:
            citations = [
                {
                    "document_id": ref.document_id,
                    "chunk_id": ref.chunk_id,
                    "score": float(ref.score) if ref.score is not None else 0.0,
                    "snippet": ref.snippet or "",
                }
                for ref in msg.references
            ]
            if not citations:
                continue
            evaluator = CitationQualityEvaluator(db)
            evaluator.evaluate_and_log(db, msg.id, citations)
            evaluated += 1
        logger.info("定时任务[引用质量评估]完成：评估消息数=%d", evaluated)
    except Exception as e:
        logger.error("定时任务[引用质量评估]失败: %s", str(e))
    finally:
        db.close()


def _run_consistency_check() -> None:
    """批量检查近期一致性问题并落库（独立 DB 会话）。"""
    db = SessionLocal()
    try:
        from datetime import datetime

        cutoff = datetime.now() - timedelta(hours=24)
        rows = (
            db.query(QaMessage)
            .filter(
                and_(
                    QaMessage.role == 2,
                    QaMessage.answer_type == 1,
                    QaMessage.created_at >= cutoff,
                    QaMessage.consistency_issues.isnot(None),
                )
            )
            .all()
        )
        logged = 0
        for msg in rows:
            try:
                issues = msg.consistency_issues or []
            except Exception:
                issues = []
            if not issues:
                continue
            for issue in issues:
                db.add(
                    ConsistencyIssueLog(
                        message_id=msg.id,
                        issue_type=str(issue.get("type") if isinstance(issue, dict) else type(issue).__name__),
                        severity=str(issue.get("severity", "medium") if isinstance(issue, dict) else "medium"),
                        description=str(issue.get("description", "") if isinstance(issue, dict) else str(issue))[:512],
                    )
                )
                logged += 1
        if logged:
            db.commit()
        logger.info("定时任务[一致性问题检查]完成：记录条数=%d", logged)
    except Exception as e:
        logger.error("定时任务[一致性问题检查]失败: %s", str(e))
    finally:
        db.close()
