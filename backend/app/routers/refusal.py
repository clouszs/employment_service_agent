"""Agent 拒答记录接口：列表查询 + 统计摘要。"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success
from app.models import AgentRefusalLog, SysUser
from app.schemas.monitor import AgentRefusalLogRead, RefusalStats

router = APIRouter(prefix="/refusal", tags=["监控-拒答记录"])


@router.get("/list", summary="拒答记录列表(分页)")
def list_refusals(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    risk_level: Optional[str] = Query(None, description="按风险等级筛选(high/medium/low)"),
    reason: Optional[str] = Query(None, description="拒答原因关键词"),
    start_date: Optional[date] = Query(None, description="起始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    """查询拒答记录（按时间倒序）。"""
    query = db.query(AgentRefusalLog)
    if risk_level:
        query = query.filter(AgentRefusalLog.query_risk_level == risk_level)
    if reason:
        query = query.filter(AgentRefusalLog.refusal_reason.ilike(f"%{reason}%"))
    if start_date:
        query = query.filter(AgentRefusalLog.created_at >= start_date)
    if end_date:
        query = query.filter(AgentRefusalLog.created_at < end_date)

    total = query.count()
    items = query.order_by(AgentRefusalLog.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return success({
        "total": total,
        "page": page,
        "size": size,
        "items": [AgentRefusalLogRead.model_validate(x).model_dump() for x in items],
    })


@router.get("/stats", summary="拒答统计摘要")
def refusal_stats(
    days: int = Query(7, ge=1, le=90, description="统计最近 N 天"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    """拒答统计：总数、今日数、按原因/风险等级分组。"""
    cutoff = date.today()  # 简单用今天做边界
    from datetime import datetime, timedelta
    cutoff_dt = datetime.now() - timedelta(days=days)

    # 总拒答数
    total = db.query(func.count(AgentRefusalLog.id)).scalar() or 0

    # 今日拒答数
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(func.count(AgentRefusalLog.id)).filter(
        AgentRefusalLog.created_at >= today_start
    ).scalar() or 0

    # 按拒答原因分组（取 refusal_reason 前 20 字做粗分组）
    reason_rows = (
        db.query(
            func.substr(AgentRefusalLog.refusal_reason, 1, 50).label("reason_prefix"),
            func.count(AgentRefusalLog.id).label("count"),
        )
        .filter(AgentRefusalLog.created_at >= cutoff_dt)
        .group_by(func.substr(AgentRefusalLog.refusal_reason, 1, 50))
        .order_by(func.count(AgentRefusalLog.id).desc())
        .limit(10)
        .all()
    )
    by_reason = [{"reason": r.reason_prefix or "未记录", "count": r.count} for r in reason_rows]

    # 按风险等级分组
    risk_rows = (
        db.query(
            AgentRefusalLog.query_risk_level,
            func.count(AgentRefusalLog.id).label("count"),
        )
        .filter(AgentRefusalLog.created_at >= cutoff_dt)
        .group_by(AgentRefusalLog.query_risk_level)
        .all()
    )
    by_risk = [
        {"risk_level": r.query_risk_level or "unknown", "count": r.count}
        for r in risk_rows
    ]

    return success(RefusalStats(
        total_refusals=total,
        today_refusals=today_count,
        by_reason=by_reason,
        by_risk_level=by_risk,
    ).model_dump())
