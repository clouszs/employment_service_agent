"""通用 schema：基类、分页参数与分页结果。"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    """可从 ORM 对象转换的响应基类。"""

    model_config = ConfigDict(from_attributes=True)


class PageParams(BaseModel):
    """分页查询参数。"""

    page: int = Field(default=1, ge=1, description="页码,从1开始")
    size: int = Field(default=20, ge=1, le=200, description="每页条数")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PageResult(BaseModel, Generic[T]):
    """分页结果包装。"""

    total: int = Field(description="总条数")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页条数")
    items: list[T] = Field(description="数据列表")
