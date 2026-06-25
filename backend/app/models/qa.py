"""问答与会话模块 ORM 模型（对应 qa_* 表）。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, JSON, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TABLE_ARGS, Base


class QaConversation(Base):
    """会话表：一次多轮对话。"""

    __tablename__ = "qa_conversation"
    __table_args__ = {"comment": "会话表：一次多轮对话", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="会话ID")
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, comment="所属用户ID(匿名可空)")
    title: Mapped[Optional[str]] = mapped_column(String(255), comment="会话标题(常取首问)")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1正常0已删除")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    messages: Mapped[list["QaMessage"]] = relationship(
        back_populates="conversation",
        primaryjoin="QaConversation.id==foreign(QaMessage.conversation_id)",
        cascade="all, delete-orphan",
    )


class QaMessage(Base):
    """消息表：对话中的每条提问/回答。"""

    __tablename__ = "qa_message"
    __table_args__ = {"comment": "消息表：每条提问/回答", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="消息ID")
    conversation_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="所属会话ID")
    role: Mapped[int] = mapped_column(SmallInteger, comment="1用户提问2系统回答")
    content: Mapped[str] = mapped_column(MEDIUMTEXT, comment="消息内容")
    rewritten_query: Mapped[Optional[str]] = mapped_column(String(1024), comment="查询改写后的问题")
    answer_type: Mapped[Optional[int]] = mapped_column(SmallInteger, comment="1知识库生成2FAQ命中3无答案兜底")
    is_no_answer: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否兜底无答案1是0否")
    llm_model: Mapped[Optional[str]] = mapped_column(String(64), comment="生成所用大模型名")
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, comment="Prompt消耗token")
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, comment="生成消耗token")
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, comment="响应耗时(毫秒)")
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), comment="综合置信度(0-1)")
    query_risk_level: Mapped[Optional[str]] = mapped_column(String(20), comment="查询风险等级(high/medium/low)")
    consistency_issues: Mapped[Optional[str]] = mapped_column(JSON, comment="一致性问题列表(JSON)")
    fact_issues: Mapped[Optional[str]] = mapped_column(JSON, comment="事实核验问题列表(JSON)")
    temporal_warnings: Mapped[Optional[str]] = mapped_column(JSON, comment="时效性警告列表(JSON)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True, comment="创建时间")

    conversation: Mapped["QaConversation"] = relationship(
        back_populates="messages",
        primaryjoin="foreign(QaMessage.conversation_id)==QaConversation.id",
    )
    references: Mapped[list["QaMessageReference"]] = relationship(
        back_populates="message",
        primaryjoin="QaMessage.id==foreign(QaMessageReference.message_id)",
        cascade="all, delete-orphan",
    )


class QaMessageReference(Base):
    """答案引用来源表：溯源核心。"""

    __tablename__ = "qa_message_reference"
    __table_args__ = {"comment": "答案引用来源表：记录命中分片,支持溯源", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    message_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="所属回答消息ID")
    document_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, comment="来源文档ID")
    chunk_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="来源分片ID")
    score: Mapped[Optional[float]] = mapped_column(Numeric(6, 4), comment="检索相关度得分")
    rank_no: Mapped[Optional[int]] = mapped_column(Integer, comment="引用排序")
    snippet: Mapped[Optional[str]] = mapped_column(Text, comment="引用片段摘要")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")

    message: Mapped["QaMessage"] = relationship(
        back_populates="references",
        primaryjoin="foreign(QaMessageReference.message_id)==QaMessage.id",
    )


class QaFeedback(Base):
    """答案反馈表：点赞/点踩，回流优化。"""

    __tablename__ = "qa_feedback"
    __table_args__ = {"comment": "答案反馈表：点赞/点踩", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    message_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="被评价的回答消息ID")
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="评价用户ID")
    rating: Mapped[int] = mapped_column(SmallInteger, comment="1点赞-1点踩")
    reason: Mapped[Optional[str]] = mapped_column(String(512), comment="点踩原因/补充")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
