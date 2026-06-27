"""系统配置模型：key-value 配置表。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TABLE_ARGS


class AppConfig(Base):
    """系统配置表。"""

    __tablename__ = "app_config"
    __table_args__ = {"comment": "系统配置（key-value）", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    config_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="配置键")
    config_value: Mapped[str] = mapped_column(Text, nullable=False, comment="配置值")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="配置说明")
    group_name: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="分组名称")
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="最后修改人ID")
    is_sensitive: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, comment="是否敏感配置（0否1是）")
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="状态（1启用0禁用）")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime | None] = mapped_column(server_default=func.now(), onupdate=func.now(), comment="更新时间")
