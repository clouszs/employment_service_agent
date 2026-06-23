"""用户反馈查询接口（管理端）：反馈明细列表 + 当日统计与近7天趋势。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success
from app.models import SysUser
from app.services import qa_service

router = APIRouter(prefix="/feedback", tags=["运营-用户反馈"])


@router.get("/stats", summary="当日反馈统计 + 近7天趋势")
def feedback_stats(
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    return success(qa_service.feedback_stats(db))


@router.get("", summary="反馈明细列表(分页)")
def list_feedback(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    rating: Optional[int] = Query(None, description="1赞 -1踩"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    rows, total = qa_service.list_feedback(
        db, offset=(page - 1) * size, limit=size, rating=rating, date_str=date
    )
    return success({"total": total, "page": page, "size": size, "items": rows})
