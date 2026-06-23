"""统计看板接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success
from app.models import SysUser
from app.services import ops_service as svc

router = APIRouter(prefix="/stats", tags=["运营-统计"])


@router.get("/overview", summary="统计概览")
def overview(
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    return success(svc.stats_overview(db))


@router.get("/hot-questions", summary="高频问题排行(按FAQ命中)")
def hot_questions(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    return success(svc.hot_questions(db, limit))
