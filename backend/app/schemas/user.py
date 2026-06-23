"""用户与权限模块 schema（对应 sys_* 表）。

枚举约定：
  user_type: 1学生 2毕业生 3辅导员 4老师 5管理员
  status:    1启用 0禁用
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


# ---------------- 用户 ----------------
class UserBase(BaseModel):
    real_name: Optional[str] = Field(default=None, max_length=64, description="真实姓名")
    user_type: int = Field(default=1, description="1学生2毕业生3辅导员4老师5管理员")
    college: Optional[str] = Field(default=None, max_length=128, description="所属学院")
    email: Optional[str] = Field(default=None, max_length=128, description="邮箱")
    phone: Optional[str] = Field(default=None, max_length=32, description="手机号")
    status: int = Field(default=1, description="1启用0禁用")


class UserCreate(UserBase):
    username: str = Field(max_length=64, description="登录账号(学工号)")
    password: str = Field(min_length=6, max_length=64, description="明文密码,服务端哈希存储")


class UserUpdate(BaseModel):
    real_name: Optional[str] = Field(default=None, max_length=64)
    user_type: Optional[int] = None
    college: Optional[str] = Field(default=None, max_length=128)
    email: Optional[str] = Field(default=None, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=32)
    status: Optional[int] = None


class UserRead(ORMModel):
    """用户响应（不含密码哈希）。"""

    id: int
    username: str
    real_name: Optional[str]
    user_type: int
    college: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    status: int
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ---------------- 角色 ----------------
class RoleBase(BaseModel):
    role_name: str = Field(max_length=64, description="角色名称")
    description: Optional[str] = Field(default=None, max_length=255, description="角色描述")


class RoleCreate(RoleBase):
    role_code: str = Field(max_length=64, description="角色编码 admin/editor/student")


class RoleUpdate(BaseModel):
    role_name: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = Field(default=None, max_length=255)


class RoleRead(ORMModel):
    id: int
    role_code: str
    role_name: str
    description: Optional[str]
    created_at: datetime


# ---------------- 用户角色关联 ----------------
class UserRoleAssign(BaseModel):
    role_ids: list[int] = Field(description="要分配的角色ID列表")


class UserRoleRead(ORMModel):
    id: int
    user_id: int
    role_id: int
    created_at: datetime


# ---------------- 密码 ----------------
class ResetPasswordRequest(BaseModel):
    """管理员重置指定用户密码。"""

    new_password: str = Field(min_length=6, max_length=64, description="新密码")


class ChangePasswordRequest(BaseModel):
    """当前登录用户自助改密码（校验旧密码）。"""

    old_password: str = Field(description="旧密码")
    new_password: str = Field(min_length=6, max_length=64, description="新密码")


# ---------------- 登录 ----------------
class LoginRequest(BaseModel):
    username: str = Field(description="登录账号")
    password: str = Field(description="密码")


class TokenResponse(BaseModel):
    access_token: str = Field(description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: UserRead = Field(description="用户信息")
