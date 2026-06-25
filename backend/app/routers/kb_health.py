"""知识库健康度接口：最新快照 + 历史记录 + 手动触发检查。"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success
from app.models import SysUser, KbHealthLog
from app.monitor.health_monitor import KnowledgeBaseHealthMonitor
from app.schemas.monitor import KbHealthLatest, KbHealthLogRead

router = APIRouter(prefix="/kb-health", tags=["监控-知识库健康度"])


@router.get("/latest", summary="知识库健康度最新快照")
def latest(
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    """获取最近一次健康检查结果。"""
    log = db.query(KbHealthLog).order_by(KbHealthLog.check_date.desc()).first()
    if not log:
        return success({
            "check_date": date.today().isoformat(),
            "health_score": 100.0,
            "warning_count": 0,
            "expired_count": 0,
            "total_docs": 0,
            "current_docs": 0,
            "avg_freshness": None,
            "created_at": None,
        })
    return success(KbHealthLatest(
        check_date=log.check_date,
        health_score=float(log.health_score or 0),
        warning_count=log.warning_docs,
        expired_count=log.expired_docs,
        total_docs=log.total_docs,
        current_docs=log.current_docs,
        avg_freshness=float(log.avg_freshness) if log.avg_freshness else None,
        created_at=log.created_at,
    ).model_dump())


@router.get("/history", summary="知识库健康度历史记录(分页)")
def history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    start_date: Optional[date] = Query(None, description="起始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    """查询健康度历史记录（按日期倒序）。"""
    query = db.query(KbHealthLog)
    if start_date:
        query = query.filter(KbHealthLog.check_date >= start_date)
    if end_date:
        query = query.filter(KbHealthLog.check_date <= end_date)

    total = query.count()
    items = query.order_by(KbHealthLog.check_date.desc()).offset((page - 1) * size).limit(size).all()

    return success({
        "total": total,
        "page": page,
        "size": size,
        "items": [KbHealthLogRead.model_validate(x).model_dump() for x in items],
    })


@router.post("/run", summary="手动触发知识库健康检查")
def run_check(
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    """立即执行一次健康检查（定时任务外的手动触发）。"""
    monitor = KnowledgeBaseHealthMonitor(db)
    report = monitor.run_daily_check()
    return success(report)
