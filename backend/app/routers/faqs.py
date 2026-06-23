"""FAQ 问答对管理接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.knowledge import FaqCreate, FaqRead, FaqUpdate
from app.services import knowledge_service as svc

router = APIRouter(prefix="/faqs", tags=["知识库-FAQ"])


@router.get("", summary="FAQ列表(分页)")
def list_faqs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = Query(None, description="问题模糊搜索"),
    category_id: Optional[int] = Query(None),
    status_: Optional[int] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = svc.list_faqs(
        db, offset=(page - 1) * size, limit=size, keyword=keyword, category_id=category_id, status=status_
    )
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [FaqRead.model_validate(f).model_dump() for f in rows],
        }
    )


@router.post("", summary="新建FAQ", status_code=status.HTTP_201_CREATED)
def create_faq(
    payload: FaqCreate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    faq = svc.create_faq(db, payload)
    return success(FaqRead.model_validate(faq).model_dump(), message="创建成功")


@router.put("/{faq_id}", summary="修改FAQ")
def update_faq(
    faq_id: int,
    payload: FaqUpdate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    faq = svc.get_faq(db, faq_id)
    if faq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ不存在")
    faq = svc.update_faq(db, faq, payload)
    return success(FaqRead.model_validate(faq).model_dump(), message="更新成功")


@router.delete("/{faq_id}", summary="删除FAQ")
def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    faq = svc.get_faq(db, faq_id)
    if faq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ不存在")
    svc.delete_faq(db, faq)
    return success(message="已删除")
