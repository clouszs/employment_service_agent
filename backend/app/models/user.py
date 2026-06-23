"""用户与权限模块 ORM 模型（对应 sys_* 表）。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TABLE_ARGS, Base


class SysUser(Base):
    """用户表：学生/老师/管理员账号。"""

    __tablename__ = "sys_user"
    __table_args__ = {"comment": "用户表：学生/老师/管理员账号", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = mapped_column(String(64), unique=True, comment="登录账号(学工号/管理员名)")
    password_hash: Mapped[Optional[str]] = mapped_column(String(128), comment="密码哈希")
    real_name: Mapped[Optional[str]] = mapped_column(String(64), comment="真实姓名")
    user_type: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1学生2毕业生3辅导员4老师5管理员")
    college: Mapped[Optional[str]] = mapped_column(String(128), comment="所属学院")
    email: Mapped[Optional[str]] = mapped_column(String(128), comment="邮箱")
    phone: Mapped[Optional[str]] = mapped_column(String(32), comment="手机号(展示脱敏)")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1启用0禁用")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="最后登录时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    roles: Mapped[list["SysUserRole"]] = relationship(
        back_populates="user",
        primaryjoin="SysUser.id==foreign(SysUserRole.user_id)",
    )


class SysRole(Base):
    """角色表：后台权限控制(RBAC)。"""

    __tablename__ = "sys_role"
    __table_args__ = {"comment": "角色表：后台权限控制(RBAC)", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="角色ID")
    role_code: Mapped[str] = mapped_column(String(64), unique=True, comment="角色编码 admin/editor/student")
    role_name: Mapped[str] = mapped_column(String(64), comment="角色名称")
    description: Mapped[Optional[str]] = mapped_column(String(255), comment="角色描述")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class SysUserRole(Base):
    """用户角色关联表：多对多。"""

    __tablename__ = "sys_user_role"
    __table_args__ = {"comment": "用户角色关联表：多对多", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="用户ID")
    role_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="角色ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")

    user: Mapped["SysUser"] = relationship(
        back_populates="roles",
        primaryjoin="foreign(SysUserRole.user_id)==SysUser.id",
    )
