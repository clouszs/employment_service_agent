"""用户简历表：保存学生生成的简历 JSON + PDF 文件路径。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TABLE_ARGS, Base


class UserResume(Base):
    """用户简历表：保存 LLM 生成的简历 JSON + PDF 路径。"""

    __tablename__ = "user_resume"
    __table_args__ = {"comment": "用户简历表", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="简历ID")
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="所属用户ID")
    title: Mapped[str] = mapped_column(String(128), comment="简历标题(如: AI算法工程师简历)")
    content: Mapped[str] = mapped_column(Text, comment="简历 JSON 原文")
    pdf_path: Mapped[Optional[str]] = mapped_column(String(512), comment="PDF 文件存储路径")
    is_default: Mapped[int] = mapped_column(Integer, default=0, comment="是否默认简历 1是0否")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
