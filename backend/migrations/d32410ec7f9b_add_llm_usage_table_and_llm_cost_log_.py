"""add llm_usage table and llm_cost_log source

Revision ID: d32410ec7f9b
Revises: fd8202321cd1
Create Date: 2026-06-28 20:29:35.542889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = 'd32410ec7f9b'
down_revision: Union[str, Sequence[str], None] = 'fd8202321cd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE_KW = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"}


def upgrade() -> None:
    """新增特性级 LLM 用量记账：llm_cost_log.source 列 + llm_usage 流水表。"""
    # 1. llm_cost_log 增加 source 列（默认 agent_chat，历史数据无痛迁移）
    op.add_column(
        "llm_cost_log",
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="agent_chat",
            comment="来源(agent_chat/resume_generation...)",
        ),
    )
    # 2. 聚合唯一性升级为 (stat_date, model, source)
    op.create_unique_constraint(
        "uq_llm_cost_date_model_source", "llm_cost_log", ["stat_date", "model", "source"]
    )
    # 3. 新建 llm_usage 流水表（特性级原始 token 记账，不存成本）
    op.create_table(
        "llm_usage",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("source", sa.String(length=32), nullable=False, comment="来源(agent_chat/resume_generation...)"),
        sa.Column("model", sa.String(length=64), nullable=False, comment="模型名"),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0", comment="输入token"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0", comment="生成token"),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=True, comment="触发用户ID"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.PrimaryKeyConstraint("id"),
        comment="LLM用量流水：特性级原始token记账",
        **_TABLE_KW,
    )
    op.create_index("ix_llm_usage_source", "llm_usage", ["source"])
    op.create_index("ix_llm_usage_created_at", "llm_usage", ["created_at"])


def downgrade() -> None:
    """回滚。"""
    op.drop_index("ix_llm_usage_created_at", table_name="llm_usage")
    op.drop_index("ix_llm_usage_source", table_name="llm_usage")
    op.drop_table("llm_usage")
    op.drop_constraint("uq_llm_cost_date_model_source", "llm_cost_log", type_="unique")
    op.drop_column("llm_cost_log", "source")
