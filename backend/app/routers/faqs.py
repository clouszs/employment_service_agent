"""FAQ 问答对管理接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import SysUser
from app.models.knowledge import KbFaq
from app.schemas.knowledge import FaqBatchAction, FaqCreate, FaqRead, FaqStatusUpdate, FaqUpdate
from app.services import knowledge_service as svc

router = APIRouter(prefix="/faqs", tags=["知识库-FAQ"])


@router.get("/top", summary="热门FAQ列表(按学生命中次数排序,学生可读)")
def top_faqs(
    size: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    """热门 FAQ：返回全部启用 FAQ，按 ask_count 降序排列。

    ask_count 是学生侧模糊命中次数（语义未命中但问法相近时累加）。
    命中 0 次的排在末尾，方便管理员识别哪些 FAQ 从未被问过。
    """
    rows = db.query(KbFaq).filter(KbFaq.status == 1).order_by(desc(KbFaq.ask_count)).limit(size).all()
    return success([FaqRead.model_validate(r).model_dump() for r in rows])


@router.post("/batch", summary="批量启用/禁用/删除FAQ")
def batch_faqs(
    payload: FaqBatchAction,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    if payload.action not in ("enable", "disable", "delete"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的操作")
    affected = 0
    for fid in payload.ids:
        faq = svc.get_faq(db, fid)
        if faq is None:
            continue
        if payload.action == "delete":
            svc.delete_faq(db, faq)
        else:
            svc.set_faq_status(db, faq, 1 if payload.action == "enable" else 0)
        affected += 1
    return success({"affected": affected}, message="批量操作完成")


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


@router.patch("/{faq_id}/status", summary="切换FAQ启用状态(轻量,不改问答文本)")
def set_faq_status(
    faq_id: int,
    payload: FaqStatusUpdate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    faq = svc.get_faq(db, faq_id)
    if faq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ不存在")
    faq = svc.set_faq_status(db, faq, payload.status)
    return success(FaqRead.model_validate(faq).model_dump(), message="状态已更新")


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
