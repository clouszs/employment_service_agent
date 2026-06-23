"""索引任务监控接口（查看解析/入库任务进度）。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models import SysUser
from app.schemas.knowledge import IndexTaskRead
from app.services import knowledge_service as svc

router = APIRouter(prefix="/index-tasks", tags=["知识库-索引任务"])


@router.get("", summary="索引任务列表(分页)")
def list_index_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    document_id: Optional[int] = Query(None),
    status_: Optional[int] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = svc.list_index_tasks(
        db, offset=(page - 1) * size, limit=size, document_id=document_id, status=status_
    )
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [IndexTaskRead.model_validate(t).model_dump() for t in rows],
        }
    )
