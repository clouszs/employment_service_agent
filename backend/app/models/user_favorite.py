"""用户收藏模型。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TABLE_ARGS


class UserFavorite(Base):
    """用户收藏表。"""

    __tablename__ = "user_favorite"
    __table_args__ = {"comment": "用户收藏", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="用户ID")
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, comment="消息ID（关联QA消息）")
    note: Mapped[str | None] = mapped_column(Text, nullable=True, comment="用户备注")
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="状态（1启用0删除）")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="收藏时间")
