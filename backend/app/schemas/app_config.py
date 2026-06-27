"""系统配置 schemas。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AppConfigBase(BaseModel):
    """系统配置基础字段。"""

    config_key: str = Field(..., max_length=128, description="配置键")
    config_value: str = Field(..., description="配置值")
    description: str | None = Field(default=None, max_length=255, description="配置说明")
    group_name: str | None = Field(default=None, max_length=64, description="分组名称")
    is_sensitive: int = Field(default=0, description="是否敏感配置（0否1是）")
    status: int = Field(default=1, description="状态（1启用0禁用）")


class AppConfigCreate(AppConfigBase):
    """新建系统配置。"""

    pass


class AppConfigUpdate(BaseModel):
    """更新系统配置（所有字段可选）。"""

    config_value: str | None = Field(default=None, description="配置值")
    description: str | None = Field(default=None, max_length=255, description="配置说明")
    group_name: str | None = Field(default=None, max_length=64, description="分组名称")
    is_sensitive: int | None = Field(default=None, description="是否敏感配置（0否1是）")
    status: int | None = Field(default=None, description="状态（1启用0禁用）")


class AppConfigRead(AppConfigBase):
    """系统配置响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="主键")
    updated_by: int | None = Field(default=None, description="最后修改人ID")
    created_at: str | None = Field(default=None, description="创建时间")
    updated_at: str | None = Field(default=None, description="更新时间")
