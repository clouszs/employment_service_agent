"""鉴权依赖：解析当前登录用户、角色校验。"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import SysRole, SysUser, SysUserRole

bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> SysUser:
    """从 Bearer Token 解析并返回当前用户。"""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效或过期的令牌")

    user = db.get(SysUser, user_id)
    if user is None or user.status != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")
    return user


def get_user_role_codes(db: Session, user_id: int) -> set[str]:
    """查询用户的角色编码集合。"""
    rows = (
        db.query(SysRole.role_code)
        .join(SysUserRole, SysUserRole.role_id == SysRole.id)
        .filter(SysUserRole.user_id == user_id)
        .all()
    )
    return {r[0] for r in rows}


def require_roles(*role_codes: str):
    """依赖工厂：要求当前用户拥有指定角色之一。"""

    def checker(
        user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> SysUser:
        owned = get_user_role_codes(db, user.id)
        if not owned.intersection(role_codes):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return user

    return checker
