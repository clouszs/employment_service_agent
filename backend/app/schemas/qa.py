"""问答与会话模块 schema（对应 qa_* 表）。

枚举约定：
  role:        1用户提问 2系统回答
  answer_type: 1知识库生成 2FAQ命中 3无答案兜底
  rating:      1点赞 -1点踩
  status:      1正常 0已删除
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


# ---------------- 会话 ----------------
class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255, description="会话标题")


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    status: Optional[int] = None


class ConversationRead(ORMModel):
    id: int
    user_id: Optional[int]
    title: Optional[str]
    status: int
    created_at: datetime
    updated_at: datetime


# ---------------- 消息 ----------------
class MessageRead(ORMModel):
    id: int
    conversation_id: int
    role: int
    content: str
    rewritten_query: Optional[str]
    answer_type: Optional[int]
    is_no_answer: int
    llm_model: Optional[str]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    latency_ms: Optional[int]
    created_at: datetime


# ---------------- 答案引用 ----------------
class MessageReferenceRead(ORMModel):
    id: int
    message_id: int
    document_id: Optional[int]
    document_title: Optional[str] = None  # 冗余存储：会话详情时回查文档表填充
    chunk_id: Optional[int]
    score: Optional[Decimal]
    rank_no: Optional[int]
    snippet: Optional[str]
    page_no: Optional[int] = None
    created_at: datetime


class MessageWithReferences(MessageRead):
    """答案消息及其引用来源（用于溯源展示）。"""

    references: list[MessageReferenceRead] = Field(default_factory=list)


class ConversationWithMessages(ConversationRead):
    """会话详情（含消息，每条消息带引用与文档标题）。"""

    messages: list[MessageWithReferences] = Field(default_factory=list)


# ---------------- 反馈 ----------------
class FeedbackCreate(BaseModel):
    rating: int = Field(description="1点赞 -1点踩")
    reason: Optional[str] = Field(default=None, max_length=512, description="点踩原因/补充")


class FeedbackRead(ORMModel):
    id: int
    message_id: int
    user_id: Optional[int]
    rating: int
    reason: Optional[str]
    created_at: datetime


# ---------------- 提问/问答（P3 接口预留的请求/响应结构）----------------
class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1024, description="用户问题")
    conversation_id: Optional[int] = Field(default=None, description="会话ID,为空则新建会话")


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1024, description="检索关键词/问题")
    top_k: int = Field(default=5, ge=1, le=50, description="返回命中条数")


class SearchHit(BaseModel):
    chunk_id: int
    document_id: int
    document_title: Optional[str] = None
    content: str
    score: float
    page_no: Optional[int] = None


class AskResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    is_no_answer: bool
    references: list[MessageReferenceRead] = Field(default_factory=list)
