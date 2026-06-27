"""用户收藏 schemas。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserFavoriteBase(BaseModel):
    """用户收藏基础字段。"""

    message_id: int | None = Field(default=None, description="消息ID")
    note: str | None = Field(default=None, description="备注")


class UserFavoriteCreate(UserFavoriteBase):
    """新建收藏。"""
    pass


class UserFavoriteUpdate(BaseModel):
    """更新收藏备注。"""

    note: str | None = Field(default=None, description="备注")


class UserFavoriteRead(UserFavoriteBase):
    """用户收藏响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="主键")
    user_id: int = Field(description="用户ID")
    status: int = Field(description="状态（1启用0删除）")
    created_at: str | None = Field(default=None, description="收藏时间")
