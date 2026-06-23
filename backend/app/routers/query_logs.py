"""问答日志查询接口（审计）。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.ops import QueryLogRead
from app.services import ops_service as svc

router = APIRouter(prefix="/logs", tags=["运营-问答日志"])


@router.get("/queries", summary="问答日志列表(分页)")
def list_query_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    user_id: Optional[int] = Query(None),
    is_no_answer: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None, description="问题模糊搜索"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    rows, total = svc.list_query_logs(
        db, (page - 1) * size, size, user_id=user_id, is_no_answer=is_no_answer, keyword=keyword
    )
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [QueryLogRead.model_validate(x).model_dump() for x in rows],
        }
    )
