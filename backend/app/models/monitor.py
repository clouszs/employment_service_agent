"""监控告警模块 ORM 模型（对应 monitor_* / kb_*_log 表）。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import BIGINT, Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.mysql import BIGINT as MYSQL_BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TABLE_ARGS, Base


class KbHealthLog(Base):
    """知识库健康度日志表：每日一条。"""

    __tablename__ = "kb_health_log"
    __table_args__ = {"comment": "知识库健康度日志：每日一条", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键")
    check_date: Mapped[date] = mapped_column(Date, nullable=False, comment="检查日期")
    total_docs: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="文档总数")
    current_docs: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="生效文档数")
    warning_docs: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="即将过期文档数(30天内)")
    expired_docs: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="已过期文档数")
    avg_freshness: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True, comment="平均新鲜度(0-1)")
    health_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True, comment="健康度评分(0-100)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")


class LlmCostLog(Base):
    """LLM 成本日志表：按天 + 模型聚合。"""

    __tablename__ = "llm_cost_log"
    __table_args__ = {"comment": "LLM成本日志：按天+模型聚合", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键")
    stat_date: Mapped[date] = mapped_column(Date, nullable=False, comment="统计日期")
    model: Mapped[str] = mapped_column(String(64), nullable=False, comment="模型名")
    call_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="调用次数")
    tokens_in: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), nullable=False, server_default="0", comment="输入token累计")
    tokens_out: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), nullable=False, server_default="0", comment="输出token累计")
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, server_default="0", comment="累计成本(USD)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")


class AgentRefusalLog(Base):
    """拒答记录表。"""

    __tablename__ = "agent_refusal_log"
    __table_args__ = {"comment": "拒答记录：用于拒答分析与持续优化", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键")
    query: Mapped[str] = mapped_column(String(1024), nullable=False, comment="被拒答的用户问题")
    refusal_reason: Mapped[str] = mapped_column(String(200), nullable=False, comment="拒答原因")
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True, comment="触发拒答时的置信度")
    query_risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="查询风险等级")
    conversation_id: Mapped[Optional[int]] = mapped_column(MYSQL_BIGINT(unsigned=True), nullable=True, comment="所属会话ID")
    user_id: Mapped[Optional[int]] = mapped_column(MYSQL_BIGINT(unsigned=True), nullable=True, comment="提问用户ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")


class CitationQualityLog(Base):
    """引用质量日志表。"""

    __tablename__ = "citation_quality_log"
    __table_args__ = {"comment": "引用质量日志：句子级引用评估结果", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键")
    message_id: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), nullable=False, comment="对应回答消息ID")
    total_sentences: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="回答句子总数")
    direct_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="direct支持句数")
    indirect_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="indirect支持句数")
    none_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", comment="无支持句数")
    avg_confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True, comment="平均引用置信度")
    quality_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True, comment="引用质量评分")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")


class ConsistencyIssueLog(Base):
    """一致性问题日志表。"""

    __tablename__ = "consistency_issue_log"
    __table_args__ = {"comment": "一致性问题日志：自我一致性检查发现的矛盾", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键")
    message_id: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), nullable=False, comment="当前回答消息ID")
    current_query: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True, comment="当前查询")
    previous_query: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True, comment="历史相似查询")
    contradiction_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="矛盾维度")
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="严重程度 high/medium/low")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")


class FactVerificationLog(Base):
    """事实核验日志表。"""

    __tablename__ = "fact_verification_log"
    __table_args__ = {"comment": "事实核验日志：政策编号/日期/金额等校验结果", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键")
    message_id: Mapped[int] = mapped_column(MYSQL_BIGINT(unsigned=True), nullable=False, comment="对应回答消息ID")
    fact_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="事实类型 policy_no/date/money/count/phone")
    extracted_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="提取到的值")
    validation_result: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="验证结果")
    suggestion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="建议修正")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
