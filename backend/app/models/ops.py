"""运营·安全·质量模块 ORM 模型（对应 op_* 表）。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TABLE_ARGS, Base


class OpQueryLog(Base):
    """问答日志表：全量审计与统计。"""

    __tablename__ = "op_query_log"
    __table_args__ = {"comment": "问答日志表：审计与统计", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, comment="用户ID")
    conversation_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="会话ID")
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="消息ID")
    question: Mapped[str] = mapped_column(String(1024), comment="用户问题")
    answer_brief: Mapped[Optional[str]] = mapped_column(String(2048), comment="答案摘要")
    hit_doc_count: Mapped[Optional[int]] = mapped_column(Integer, comment="命中文档数")
    is_no_answer: Mapped[int] = mapped_column(SmallInteger, default=0, index=True, comment="是否无答案1是0否")
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, comment="总耗时(毫秒)")
    client_ip: Mapped[Optional[str]] = mapped_column(String(64), comment="客户端IP")
    channel: Mapped[Optional[str]] = mapped_column(String(32), comment="来源渠道web/h5/wecom")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True, comment="创建时间")


class OpSensitiveWord(Base):
    """敏感词表：提问内容合规过滤。"""

    __tablename__ = "op_sensitive_word"
    __table_args__ = {"comment": "敏感词表：合规过滤", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    word: Mapped[str] = mapped_column(String(128), unique=True, comment="敏感词/违规词")
    category: Mapped[Optional[str]] = mapped_column(String(64), comment="分类")
    action: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1拦截2替换3告警")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1启用0禁用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class OpUnansweredQuestion(Base):
    """无答案问题专项记录：检索/生成未找到答案的问题，供优化知识库。"""

    __tablename__ = "op_unanswered_question"
    __table_args__ = {"comment": "无答案问题专项记录(合并计数+处理状态)", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    question: Mapped[str] = mapped_column(String(1024), comment="未找到答案的问题")
    question_hash: Mapped[str] = mapped_column(String(64), unique=True, comment="问题SHA-256,合并相同问题")
    ask_count: Mapped[int] = mapped_column(Integer, default=1, comment="出现次数")
    last_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="最近提问用户ID")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, index=True, comment="处理状态:1未解决 2已解决")
    resolve_note: Mapped[Optional[str]] = mapped_column(String(512), comment="处理说明")
    first_asked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="首次提问时间")
    last_asked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="最近提问时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class OpEvalCase(Base):
    """评测集表：回归测试准确率/召回率。"""

    __tablename__ = "op_eval_case"
    __table_args__ = {"comment": "评测集表：质量回归", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    question: Mapped[str] = mapped_column(String(1024), comment="评测问题")
    expected_answer: Mapped[Optional[str]] = mapped_column(Text, comment="参考标准答案")
    expected_doc_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="期望命中文档ID")
    category: Mapped[Optional[str]] = mapped_column(String(64), comment="问题类别")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1启用0禁用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
