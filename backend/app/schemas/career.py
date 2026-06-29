"""生涯服务（简历/职位/日历）请求与响应 Schema。"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ===== 简历 =====
class ResumeGenerateRequest(BaseModel):
    target_job: str = Field("", max_length=128, description="目标岗位")
    extra_profile: Optional[dict[str, Any]] = Field(
        default=None, description="前端补充档案（major/skills/experience 等自由字段）"
    )


# ===== 职位推荐 =====
class JobQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=128, description="关键词/岗位方向")
    top_k: int = Field(5, ge=1, le=20, description="返回条数")
    location: Optional[str] = Field(None, max_length=64, description="地点过滤")


# ===== 日历 =====
class CalendarIcsRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=128, description="事件标题")
    start_time: str = Field(..., description="开始时间 ISO 8601")
    end_time: Optional[str] = Field(None, description="结束时间 ISO 8601（缺省 +1h）")
    location: str = Field("", max_length=128)
    description: str = Field("", max_length=512)
