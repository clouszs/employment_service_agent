"""用户管理接口（需登录；增删改建议管理员权限）。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.user import (
    ResetPasswordRequest,
    RoleRead,
    UserCreate,
    UserRead,
    UserRoleAssign,
    UserUpdate,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", summary="用户列表(分页)")
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    keyword: str | None = Query(None, description="账号/姓名模糊搜索"),
    user_type: int | None = Query(None),
    status_: int | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = user_service.list_users(
        db, offset=(page - 1) * size, limit=size, keyword=keyword, user_type=user_type, status=status_
    )
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [UserRead.model_validate(u).model_dump() for u in rows],
        }
    )


@router.get("/{user_id}", summary="用户详情")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return success(UserRead.model_validate(user).model_dump())


@router.post("", summary="新建用户", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    if user_service.get_user_by_username(db, payload.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账号已存在")
    try:
        user = user_service.create_user(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账号已存在")
    return success(UserRead.model_validate(user).model_dump(), message="创建成功")


@router.put("/{user_id}", summary="修改用户")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user = user_service.update_user(db, user, payload)
    return success(UserRead.model_validate(user).model_dump(), message="更新成功")


@router.delete("/{user_id}", summary="禁用用户(软删除)")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user_service.disable_user(db, user)
    return success(message="已禁用")


@router.delete("/{user_id}/permanent", summary="物理删除用户(彻底移除)")
def hard_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    roles = {r.role_code for r in user_service.list_user_roles(db, user_id)}
    if "admin" in roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不可删除管理员账户")
    user_service.hard_delete_user(db, user)
    return success(message="已彻底删除")


@router.post("/{user_id}/reset-password", summary="重置用户密码(管理员)")
def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user_service.reset_password(db, user, payload.new_password)
    return success(message="密码已重置")


@router.get("/{user_id}/roles", summary="查看用户角色")
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    if user_service.get_user(db, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    roles = user_service.list_user_roles(db, user_id)
    return success([RoleRead.model_validate(r).model_dump() for r in roles])


@router.put("/{user_id}/roles", summary="分配用户角色")
def assign_user_roles(
    user_id: int,
    payload: UserRoleAssign,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    if user_service.get_user(db, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user_service.assign_roles(db, user_id, payload.role_ids)
    roles = user_service.list_user_roles(db, user_id)
    return success([RoleRead.model_validate(r).model_dump() for r in roles], message="分配成功")
