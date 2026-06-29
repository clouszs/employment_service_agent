"""LLM 用量流水模型（特性级原始记账）。

记录「非对话类」LLM 调用（如简历生成）的原始 token 用量，由 cost_monitor 在每日
聚合时按 (model, source) 汇总进 llm_cost_log。流水表只存原始量，不存成本——价格表
变动时重聚合即可修正历史。source 用 VARCHAR 存储（非 DB ENUM），新增来源零 DDL。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.mysql import BIGINT as MYSQL_BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TABLE_ARGS, Base


class LlmUsageSource(str, Enum):
    """LLM 用量来源（共享词表，供流水写入与成本聚合打标使用）。"""

    AGENT_CHAT = "agent_chat"  # Agent 对话流水线（实际从 QaMessage 聚合，此处仅作聚合打标常量）
    RESUME_GENERATION = "resume_generation"  # 简历生成


class LlmUsage(Base):
    """LLM 用量流水表：每次特性级 LLM 调用一条原始记录。"""

    __tablename__ = "llm_usage"
    __table_args__ = {"comment": "LLM用量流水：特性级原始token记账", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键")
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="来源(agent_chat/resume_generation...)")
    model: Mapped[str] = mapped_column(String(64), nullable=False, comment="模型名")
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="输入token")
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="生成token")
    user_id: Mapped[Optional[int]] = mapped_column(MYSQL_BIGINT(unsigned=True), nullable=True, comment="触发用户ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True, comment="创建时间"
    )
