"""监控告警模块 schema（对应 monitor_* / kb_*_log 表）。

模块划分：
  kb_health  —— 知识库健康度
  llm_cost   —— LLM 成本统计
  refusal    —— Agent 拒答记录
  citation   —— 引用质量评估
  consistency —— 一致性问题
  fact_verify  —— 事实核验
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


# ==================== 知识库健康度 ====================


class KbHealthLogRead(ORMModel):
    """知识库健康度日志（单条）。"""

    id: int
    check_date: date
    total_docs: int
    current_docs: int
    warning_docs: int
    expired_docs: int
    avg_freshness: Optional[float]
    health_score: Optional[float]
    created_at: datetime


class KbHealthLatest(BaseModel):
    """知识库健康度最新快照。"""

    check_date: date = Field(description="检查日期")
    health_score: float = Field(description="健康度评分(0-100)")
    warning_count: int = Field(description="即将过期文档数")
    expired_count: int = Field(description="已过期文档数")
    total_docs: int = Field(description="文档总数")
    current_docs: int = Field(description="生效文档数")
    avg_freshness: Optional[float] = Field(default=None, description="平均新鲜度(0-1)")
    created_at: datetime


# ==================== LLM 成本 ====================


class LlmCostLogRead(ORMModel):
    """LLM 成本日志（按天+模型聚合，单条）。"""

    id: int
    stat_date: date
    model: str
    source: str
    call_count: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    created_at: datetime
    updated_at: datetime


class LlmCostSourceBreakdown(BaseModel):
    """按来源拆分的成本项。"""

    source: str = Field(description="来源(agent_chat/resume_generation...)")
    call_count: int = Field(description="调用次数")
    tokens_in: int = Field(description="输入 token")
    tokens_out: int = Field(description="输出 token")
    cost_usd: float = Field(description="成本(USD)")


class LlmCostMonthlySourceRead(BaseModel):
    """单月成本按来源拆分。"""

    year: int = Field(description="年份")
    month: int = Field(description="月份")
    total_cost_usd: float = Field(description="当月总成本(USD)")
    sources: list[LlmCostSourceBreakdown] = Field(default_factory=list, description="按来源拆分")


class LlmCostDailyRead(BaseModel):
    """单日成本汇总。"""

    stat_date: date = Field(description="统计日期")
    total_cost_usd: float = Field(description="当日总成本(USD)")
    total_calls: int = Field(description="当日总调用次数")
    total_tokens_in: int = Field(description="当日总输入 token")
    total_tokens_out: int = Field(description="当日总输出 token")
    models: list[dict] = Field(default_factory=list, description="按模型拆分")
    sources: list[LlmCostSourceBreakdown] = Field(default_factory=list, description="按来源拆分")


class LlmCostMonthlyRead(BaseModel):
    """单月成本汇总。"""

    year: int = Field(description="年份")
    month: int = Field(description="月份")
    total_cost_usd: float = Field(description="当月总成本(USD)")
    models: list[dict] = Field(default_factory=list, description="按模型拆分")


# ==================== 拒答记录 ====================


class AgentRefusalLogRead(ORMModel):
    """拒答记录（单条）。"""

    id: int
    query: str
    refusal_reason: str
    confidence: Optional[float]
    query_risk_level: Optional[str]
    conversation_id: Optional[int]
    user_id: Optional[int]
    created_at: datetime


class RefusalStats(BaseModel):
    """拒答统计摘要。"""

    total_refusals: int = Field(description="拒答总次数")
    today_refusals: int = Field(description="今日拒答次数")
    by_reason: list[dict] = Field(default_factory=list, description="按拒答原因分组")
    by_risk_level: list[dict] = Field(default_factory=list, description="按风险等级分组")


# ==================== 引用质量 ====================


class CitationQualityLogRead(ORMModel):
    """引用质量日志（单条）。"""

    id: int
    message_id: int
    total_sentences: int
    direct_count: int
    indirect_count: int
    none_count: int
    avg_confidence: Optional[float]
    quality_score: Optional[float]
    created_at: datetime


# ==================== 一致性问题 ====================


class ConsistencyIssueLogRead(ORMModel):
    """一致性问题日志（单条）。"""

    id: int
    message_id: int
    current_query: Optional[str]
    previous_query: Optional[str]
    contradiction_type: Optional[str]
    severity: Optional[str]
    created_at: datetime


# ==================== 事实核验 ====================


class FactVerificationLogRead(ORMModel):
    """事实核验日志（单条）。"""

    id: int
    message_id: int
    fact_type: str
    extracted_value: Optional[str]
    validation_result: Optional[str]
    suggestion: Optional[str]
    created_at: datetime
