"""LLM 成本统计接口：单日汇总 + 月度汇总 + 历史记录。"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success
from app.models import LlmCostLog, SysUser
from app.monitor.cost_monitor import LlmCostMonitor
from app.schemas.monitor import LlmCostDailyRead, LlmCostMonthlyRead, LlmCostLogRead

router = APIRouter(prefix="/llm-cost", tags=["监控-LLM成本"])


@router.get("/daily", summary="LLM 单日成本汇总")
def daily(
    stat_date: Optional[date] = Query(None, description="统计日期，默认今天"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    """获取指定日期的 LLM 成本汇总（按模型拆分）。

    如果该日期尚无统计数据，自动触发一次成本统计后返回。
    """
    target = stat_date or date.today()

    # 检查是否已有数据，没有则自动生成
    existing = db.scalar(
        db.query(LlmCostLog.id).filter(LlmCostLog.stat_date == target).limit(1)
    )
    if not existing:
        monitor = LlmCostMonitor(db)
        monitor.run_daily_check(target)

    # 查询该日期的聚合数据
    rows = (
        db.query(
            LlmCostLog.stat_date,
            LlmCostLog.model,
            LlmCostLog.call_count,
            LlmCostLog.tokens_in,
            LlmCostLog.tokens_out,
            LlmCostLog.cost_usd,
        )
        .filter(LlmCostLog.stat_date == target)
        .all()
    )

    models = [
        {
            "model": r.model,
            "call_count": r.call_count,
            "tokens_in": r.tokens_in,
            "tokens_out": r.tokens_out,
            "cost_usd": round(float(r.cost_usd), 4),
        }
        for r in rows
    ]

    result = LlmCostDailyRead(
        stat_date=target,
        total_cost_usd=round(sum(m["cost_usd"] for m in models), 4),
        total_calls=sum(m["call_count"] for m in models),
        total_tokens_in=sum(m["tokens_in"] for m in models),
        total_tokens_out=sum(m["tokens_out"] for m in models),
        models=models,
    )
    return success(result.model_dump())


@router.get("/monthly", summary="LLM 月度成本汇总")
def monthly(
    year: int = Query(..., ge=2000, le=2100, description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    """获取指定月份的 LLM 成本汇总（按模型拆分）。"""
    monitor = LlmCostMonitor(db)
    report = monitor.get_monthly_cost(year, month)
    result = LlmCostMonthlyRead(
        year=report["year"],
        month=report["month"],
        total_cost_usd=report["total_cost_usd"],
        models=report["models"],
    )
    return success(result.model_dump())


@router.get("/history", summary="LLM 成本日志列表(分页)")
def history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    model: Optional[str] = Query(None, description="按模型名筛选"),
    start_date: Optional[date] = Query(None, description="起始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    """查询 LLM 成本日志历史（按日期倒序）。"""
    query = db.query(LlmCostLog)
    if model:
        query = query.filter(LlmCostLog.model == model)
    if start_date:
        query = query.filter(LlmCostLog.stat_date >= start_date)
    if end_date:
        query = query.filter(LlmCostLog.stat_date <= end_date)

    total = query.count()
    items = query.order_by(LlmCostLog.stat_date.desc()).offset((page - 1) * size).limit(size).all()

    return success({
        "total": total,
        "page": page,
        "size": size,
        "items": [LlmCostLogRead.model_validate(x).model_dump() for x in items],
    })
