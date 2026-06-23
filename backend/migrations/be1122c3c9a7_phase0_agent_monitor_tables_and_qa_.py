"""phase0 agent monitor tables and qa_message fields

阶段 0 迁移：监控告警模块的 6 张日志表 + qa_message 五重防护字段扩展。

一、新增 6 张写多读少的日志表（全部 InnoDB / utf8mb4，BIGINT UNSIGNED 自增主键）：
  1. kb_health_log         知识库健康度日志（每日一条，check_date 唯一）
  2. llm_cost_log          LLM 成本日志（按天 + 模型聚合，(stat_date, model) 唯一）
  3. agent_refusal_log     拒答记录
  4. citation_quality_log  引用质量日志
  5. consistency_issue_log 一致性问题日志
  6. fact_verification_log 事实核验日志

二、qa_message 表字段扩展（完整集，一步到位）：
  - confidence          DECIMAL(5,4)  综合置信度
  - query_risk_level    VARCHAR(20)   查询风险等级 high/medium/low
  - consistency_issues  JSON          自我一致性检查问题列表
  - fact_issues         JSON          事实核验问题列表
  - temporal_warnings   JSON          时效性警告列表
  （prompt_tokens / completion_tokens / latency_ms 已存在，复用，不新增）

Revision ID: be1122c3c9a7
Revises: 83dc52f295f1
Create Date: 2026-06-23 21:07:46.401709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = "be1122c3c9a7"
down_revision: Union[str, Sequence[str], None] = "83dc52f295f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 与现有业务表保持一致的建表参数
_TABLE_KW = dict(
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
    mysql_collate="utf8mb4_0900_ai_ci",
)


def upgrade() -> None:
    """Upgrade schema：建 6 张日志表 + 给 qa_message 加 5 个字段。"""

    # ---------------- 1. kb_health_log ----------------
    op.create_table(
        "kb_health_log",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键"),
        sa.Column("check_date", sa.Date(), nullable=False, comment="检查日期"),
        sa.Column("total_docs", sa.Integer(), nullable=False, server_default="0", comment="文档总数"),
        sa.Column("current_docs", sa.Integer(), nullable=False, server_default="0", comment="生效文档数"),
        sa.Column("warning_docs", sa.Integer(), nullable=False, server_default="0", comment="即将过期文档数(30天内)"),
        sa.Column("expired_docs", sa.Integer(), nullable=False, server_default="0", comment="已过期文档数"),
        sa.Column("avg_freshness", sa.Numeric(5, 4), nullable=True, comment="平均新鲜度(0-1)"),
        sa.Column("health_score", sa.Numeric(5, 2), nullable=True, comment="健康度评分(0-100)"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.UniqueConstraint("check_date", name="uk_kb_health_check_date"),
        comment="知识库健康度日志：每日一条",
        **_TABLE_KW,
    )

    # ---------------- 2. llm_cost_log ----------------
    op.create_table(
        "llm_cost_log",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键"),
        sa.Column("stat_date", sa.Date(), nullable=False, comment="统计日期"),
        sa.Column("model", sa.String(64), nullable=False, comment="模型名"),
        sa.Column("call_count", sa.Integer(), nullable=False, server_default="0", comment="调用次数"),
        sa.Column("tokens_in", mysql.BIGINT(unsigned=True), nullable=False, server_default="0", comment="输入token累计"),
        sa.Column("tokens_out", mysql.BIGINT(unsigned=True), nullable=False, server_default="0", comment="输出token累计"),
        sa.Column("cost_usd", sa.Numeric(10, 4), nullable=False, server_default="0", comment="累计成本(USD)"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False, comment="更新时间"),
        sa.UniqueConstraint("stat_date", "model", name="uk_llm_cost_date_model"),
        comment="LLM成本日志：按天+模型聚合",
        **_TABLE_KW,
    )

    # ---------------- 3. agent_refusal_log ----------------
    op.create_table(
        "agent_refusal_log",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键"),
        sa.Column("query", sa.Text(), nullable=False, comment="被拒答的用户问题"),
        sa.Column("refusal_reason", sa.String(200), nullable=False, comment="拒答原因"),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True, comment="触发拒答时的置信度"),
        sa.Column("query_risk_level", sa.String(20), nullable=True, comment="查询风险等级"),
        sa.Column("conversation_id", mysql.BIGINT(unsigned=True), nullable=True, comment="所属会话ID"),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=True, comment="提问用户ID"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Index("idx_agent_refusal_created", "created_at"),
        comment="拒答记录：用于拒答分析与持续优化",
        **_TABLE_KW,
    )

    # ---------------- 4. citation_quality_log ----------------
    op.create_table(
        "citation_quality_log",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键"),
        sa.Column("message_id", mysql.BIGINT(unsigned=True), nullable=False, comment="对应回答消息ID"),
        sa.Column("total_sentences", sa.Integer(), nullable=False, server_default="0", comment="回答句子总数"),
        sa.Column("direct_count", sa.Integer(), nullable=False, server_default="0", comment="direct支持句数"),
        sa.Column("indirect_count", sa.Integer(), nullable=False, server_default="0", comment="indirect支持句数"),
        sa.Column("none_count", sa.Integer(), nullable=False, server_default="0", comment="无支持句数"),
        sa.Column("avg_confidence", sa.Numeric(5, 4), nullable=True, comment="平均引用置信度"),
        sa.Column("quality_score", sa.Numeric(5, 4), nullable=True, comment="引用质量评分"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Index("idx_citation_quality_message", "message_id"),
        comment="引用质量日志：句子级引用评估结果",
        **_TABLE_KW,
    )

    # ---------------- 5. consistency_issue_log ----------------
    op.create_table(
        "consistency_issue_log",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键"),
        sa.Column("message_id", mysql.BIGINT(unsigned=True), nullable=False, comment="当前回答消息ID"),
        sa.Column("current_query", sa.String(1024), nullable=True, comment="当前查询"),
        sa.Column("previous_query", sa.String(1024), nullable=True, comment="历史相似查询"),
        sa.Column("contradiction_type", sa.String(50), nullable=True, comment="矛盾维度"),
        sa.Column("severity", sa.String(20), nullable=True, comment="严重程度 high/medium/low"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Index("idx_consistency_message", "message_id"),
        comment="一致性问题日志：自我一致性检查发现的矛盾",
        **_TABLE_KW,
    )

    # ---------------- 6. fact_verification_log ----------------
    op.create_table(
        "fact_verification_log",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键"),
        sa.Column("message_id", mysql.BIGINT(unsigned=True), nullable=False, comment="对应回答消息ID"),
        sa.Column("fact_type", sa.String(30), nullable=False, comment="事实类型 policy_no/date/money/count/phone"),
        sa.Column("extracted_value", sa.String(255), nullable=True, comment="提取到的值"),
        sa.Column("validation_result", sa.String(255), nullable=True, comment="验证结果"),
        sa.Column("suggestion", sa.String(255), nullable=True, comment="建议修正"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Index("idx_fact_verify_message", "message_id"),
        comment="事实核验日志：政策编号/日期/金额等校验结果",
        **_TABLE_KW,
    )

    # ---------------- qa_message 字段扩展 ----------------
    op.add_column("qa_message", sa.Column("confidence", sa.Numeric(5, 4), nullable=True, comment="综合置信度"))
    op.add_column("qa_message", sa.Column("query_risk_level", sa.String(20), nullable=True, comment="查询风险等级 high/medium/low"))
    op.add_column("qa_message", sa.Column("consistency_issues", sa.JSON(), nullable=True, comment="自我一致性检查问题列表(JSON)"))
    op.add_column("qa_message", sa.Column("fact_issues", sa.JSON(), nullable=True, comment="事实核验问题列表(JSON)"))
    op.add_column("qa_message", sa.Column("temporal_warnings", sa.JSON(), nullable=True, comment="时效性警告列表(JSON)"))


def downgrade() -> None:
    """Downgrade schema：回滚 qa_message 字段 + 删除 6 张日志表。"""
    op.drop_column("qa_message", "temporal_warnings")
    op.drop_column("qa_message", "fact_issues")
    op.drop_column("qa_message", "consistency_issues")
    op.drop_column("qa_message", "query_risk_level")
    op.drop_column("qa_message", "confidence")

    op.drop_table("fact_verification_log")
    op.drop_table("consistency_issue_log")
    op.drop_table("citation_quality_log")
    op.drop_table("agent_refusal_log")
    op.drop_table("llm_cost_log")
    op.drop_table("kb_health_log")
