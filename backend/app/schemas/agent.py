"""Agent 对话模块 schema（对应 agent_* 接口 + QaMessage Agent 扩展字段）。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


# ==================== 请求 ====================


class AgentChatRequest(BaseModel):
    """Agent 同步对话请求。"""

    query: str = Field(min_length=1, max_length=1024, description="用户问题")
    conversation_id: Optional[int] = Field(default=None, description="会话ID，为空则新建")


# ==================== 响应 ====================


class AgentChatResponse(BaseModel):
    """Agent 同步对话响应。"""

    conversation_id: int = Field(description="会话ID")
    message_id: int = Field(description="AI 回答消息ID")
    response: str = Field(description="回答内容")
    confidence: float = Field(description="综合置信度(0-1)")
    is_no_answer: bool = Field(description="是否无答案/拒答")
    route: str = Field(description="路由决策(search/direct/refuse/regenerated/cached/error)")
    query_risk_level: str = Field(description="查询风险等级(high/medium/low)")
    is_low_confidence: bool = Field(description="是否低置信度降级回答")
    is_error: bool = Field(description="是否出错")
    citations: list[dict] = Field(default_factory=list, description="引用来源列表")
    consistency_issues: list[dict] = Field(default_factory=list, description="一致性问题列表")
    fact_issues: list[dict] = Field(default_factory=list, description="事实核验问题列表")
    temporal_warnings: list[str] = Field(default_factory=list, description="时效性警告列表")
    warnings: list[str] = Field(default_factory=list, description="警告列表")
    request_id: str = Field(description="请求ID(幂等键)")
    llm_tokens_in: int = Field(default=0, description="Prompt Token 数")
    llm_tokens_out: int = Field(default=0, description="生成 Token 数")
