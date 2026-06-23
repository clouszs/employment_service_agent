"""角色管理接口。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.user import RoleCreate, RoleRead, RoleUpdate
from app.services import user_service

router = APIRouter(prefix="/roles", tags=["角色管理"])


@router.get("", summary="角色列表")
def list_roles(
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    roles = user_service.list_roles(db)
    return success([RoleRead.model_validate(r).model_dump() for r in roles])


@router.post("", summary="新建角色", status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    if user_service.get_role_by_code(db, payload.role_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色编码已存在")
    try:
        role = user_service.create_role(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色编码已存在")
    return success(RoleRead.model_validate(role).model_dump(), message="创建成功")


@router.put("/{role_id}", summary="修改角色")
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    role = user_service.get_role(db, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    role = user_service.update_role(db, role, payload)
    return success(RoleRead.model_validate(role).model_dump(), message="更新成功")
