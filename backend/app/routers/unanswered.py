"""无答案问题专项管理接口（管理端）：列表、标记已解决/未解决、删除。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.ops import UnansweredRead, UnansweredResolve
from app.services import ops_service

router = APIRouter(prefix="/unanswered", tags=["运营-无答案问题"])


@router.get("", summary="无答案问题列表(分页)")
def list_unanswered(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    status_: Optional[int] = Query(None, alias="status", description="1未解决 2已解决"),
    keyword: Optional[str] = Query(None, description="问题模糊搜索"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    rows, total = ops_service.list_unanswered(
        db, offset=(page - 1) * size, limit=size, status=status_, keyword=keyword
    )
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [UnansweredRead.model_validate(x).model_dump() for x in rows],
        }
    )


@router.put("/{item_id}", summary="标记处理状态(已解决/未解决)+说明")
def resolve_unanswered(
    item_id: int,
    payload: UnansweredResolve,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    obj = ops_service.get_unanswered(db, item_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")
    if payload.status not in (1, 2):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status 只能为 1 或 2")
    obj = ops_service.resolve_unanswered(db, obj, payload.status, payload.resolve_note)
    return success(UnansweredRead.model_validate(obj).model_dump(), message="已更新")


@router.delete("/{item_id}", summary="删除记录")
def delete_unanswered(
    item_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    obj = ops_service.get_unanswered(db, item_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")
    ops_service.delete_unanswered(db, obj)
    return success(message="已删除")
