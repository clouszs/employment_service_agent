"""敏感词管理接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.ops import SensitiveWordCreate, SensitiveWordRead, SensitiveWordUpdate
from app.services import ops_service as svc

router = APIRouter(prefix="/sensitive-words", tags=["运营-敏感词"])


@router.get("", summary="敏感词列表(分页)")
def list_words(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = Query(None),
    status_: Optional[int] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = svc.list_sensitive_words(db, (page - 1) * size, size, keyword=keyword, status=status_)
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [SensitiveWordRead.model_validate(w).model_dump() for w in rows],
        }
    )


@router.post("", summary="新建敏感词", status_code=status.HTTP_201_CREATED)
def create_word(
    payload: SensitiveWordCreate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    if svc.get_sensitive_word_by_text(db, payload.word):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="敏感词已存在")
    obj = svc.create_sensitive_word(db, payload)
    return success(SensitiveWordRead.model_validate(obj).model_dump(), message="创建成功")


@router.put("/{word_id}", summary="修改敏感词")
def update_word(
    word_id: int,
    payload: SensitiveWordUpdate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    obj = svc.get_sensitive_word(db, word_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="敏感词不存在")
    obj = svc.update_sensitive_word(db, obj, payload)
    return success(SensitiveWordRead.model_validate(obj).model_dump(), message="更新成功")


@router.delete("/{word_id}", summary="删除敏感词")
def delete_word(
    word_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    obj = svc.get_sensitive_word(db, word_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="敏感词不存在")
    svc.delete_sensitive_word(db, obj)
    return success(message="已删除")
