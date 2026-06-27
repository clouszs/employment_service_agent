"""公告 schemas。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnnouncementBase(BaseModel):
    """公告基础字段。"""

    title: str = Field(..., max_length=200, description="公告标题")
    content: str = Field(..., description="公告内容")
    priority: int = Field(default=2, description="优先级（1高2中3低）")
    status: int = Field(default=1, description="状态（0草稿1发布2撤下）")


class AnnouncementCreate(AnnouncementBase):
    """新建公告。"""

    expire_at: datetime | None = Field(default=None, description="过期时间")


class AnnouncementUpdate(BaseModel):
    """更新公告（所有字段可选）。"""

    title: str | None = Field(default=None, max_length=200, description="公告标题")
    content: str | None = Field(default=None, description="公告内容")
    priority: int | None = Field(default=None, description="优先级（1高2中3低）")
    expire_at: datetime | None = Field(default=None, description="过期时间")
    status: int | None = Field(default=None, description="状态（0草稿1发布2撤下）")


class AnnouncementRead(AnnouncementBase):
    """公告响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="主键")
    expire_at: datetime | None = Field(default=None, description="过期时间")
    created_by: int | None = Field(default=None, description="发布人ID")
    created_at: datetime | None = Field(default=None, description="创建时间")
    updated_at: datetime | None = Field(default=None, description="更新时间")
