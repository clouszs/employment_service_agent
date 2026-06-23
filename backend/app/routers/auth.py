"""认证接口：登录、获取当前用户。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.core.response import success
from app.models import SysUser
from app.schemas.user import ChangePasswordRequest, LoginRequest, UserRead
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", summary="登录获取令牌")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = user_service.authenticate(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    token = create_access_token(subject=user.id, extra={"username": user.username})
    return success(
        {
            "access_token": token,
            "token_type": "bearer",
            "user": UserRead.model_validate(user).model_dump(),
        },
        message="登录成功",
    )


@router.get("/me", summary="获取当前登录用户")
def me(current: SysUser = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    roles = [r.role_code for r in user_service.list_user_roles(db, current.id)]
    data = UserRead.model_validate(current).model_dump()
    data["roles"] = roles
    return success(data)


@router.post("/change-password", summary="修改自己的密码(校验旧密码)")
def change_password(
    payload: ChangePasswordRequest,
    current: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    ok = user_service.change_password(db, current, payload.old_password, payload.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码不正确")
    return success(message="密码修改成功")
