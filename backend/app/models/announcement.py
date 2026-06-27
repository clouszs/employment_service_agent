"""公告模型。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TABLE_ARGS


class Announcement(Base):
    """公告表。"""

    __tablename__ = "announcement"
    __table_args__ = {"comment": "系统公告", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="公告标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="公告内容")
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=2, comment="优先级（1高2中3低）")
    publish_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="定时发布时间")
    expire_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="过期时间")
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="状态（0草稿1发布2撤下）")
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="发布人ID")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
