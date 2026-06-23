"""文档分类管理接口。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.knowledge import CategoryCreate, CategoryRead, CategoryUpdate
from app.services import knowledge_service as svc

router = APIRouter(prefix="/categories", tags=["知识库-分类"])


@router.get("", summary="分类列表")
def list_categories(db: Session = Depends(get_db), _: SysUser = Depends(get_current_user)) -> dict:
    rows = svc.list_categories(db)
    return success([CategoryRead.model_validate(c).model_dump() for c in rows])


@router.post("", summary="新建分类", status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    cat = svc.create_category(db, payload)
    return success(CategoryRead.model_validate(cat).model_dump(), message="创建成功")


@router.put("/{category_id}", summary="修改分类")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    cat = svc.get_category(db, category_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    cat = svc.update_category(db, cat, payload)
    return success(CategoryRead.model_validate(cat).model_dump(), message="更新成功")


@router.delete("/{category_id}", summary="删除分类")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    cat = svc.get_category(db, category_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    if svc.has_children(db, category_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="存在子分类或关联文档，不可删除")
    svc.delete_category(db, cat)
    return success(message="已删除")
