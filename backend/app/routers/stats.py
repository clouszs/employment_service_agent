"""统计看板接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success
from app.models import SysUser
from app.services import ops_service as svc
from app.services import user_service

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


@router.get("/daily", summary="仪表盘日维度KPI(只读聚合)")
def daily(
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    return success(svc.stats_daily(db))


@router.get("/trend", summary="对话趋势-最近N天每日提问数(只读聚合)")
def trend(
    days: int = Query(14, ge=2, le=60),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    return success(svc.stats_trend(db, days))


@router.get("/activity", summary="最近活动时间线(聚合现有表近期事件)")
def activity(
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    return success(svc.recent_activity(db, limit))


@router.get("/employment", summary="就业数据统计(学生可读,教师可筛选)")
def employment(
    department: str | None = Query(None, description="院系筛选(仅教师/管理员)"),
    grade: str | None = Query(None, description="年级筛选(仅教师/管理员)"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin", "editor", "student")),
) -> dict:
    """就业数据统计 - 学生看全局聚合,教师可按院系/年级筛选。

    返回维度: 就业率趋势(按年份) + 行业分布 + 薪资分布 + 地域分布
    """
    # 学生无筛选权限,忽略筛选参数
    role_codes = {r.role_code for r in user_service.list_user_roles(db, current_user.id)}
    if "admin" not in role_codes and "editor" not in role_codes:
        department = None
        grade = None

    return success(svc.stats_employment(department, grade))
