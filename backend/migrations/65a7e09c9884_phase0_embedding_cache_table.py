"""phase0 embedding cache table

阶段 0 迁移：Embedding 缓存 L3 持久层（方案 B 三级缓存的最底层兜底）。

缓存链路：L1 进程内存(LRU) → L2 Redis(TTL 24h) → L3 本表(MySQL 持久) → DashScope API
本表作用：即使 Redis 宕机，已算过的向量仍能从 MySQL 命中，避免重复调用收费的 Embedding API。

表设计：
  - cache_key   文本+模型+维度 的 SHA256（唯一键，定长 64）
  - text_sample 原文前 200 字（仅排查用，不参与命中）
  - model       生成所用 embedding 模型名
  - dim         向量维度
  - embedding   向量本体，JSON 字符串存于 LONGTEXT（精确往返，避免 MySQL 原生 JSON 类型
                对 double 归一化造成的 1-ULP 偏差；向量内部不做 JSON 查询，用 LONGTEXT 无损失）
  - hit_count   命中次数（便于做缓存淘汰分析）
  - created_at / updated_at

Revision ID: 65a7e09c9884
Revises: be1122c3c9a7
Create Date: 2026-06-23 21:12:27.512845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = "65a7e09c9884"
down_revision: Union[str, Sequence[str], None] = "be1122c3c9a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE_KW = dict(
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
    mysql_collate="utf8mb4_0900_ai_ci",
)


def upgrade() -> None:
    """Upgrade schema：创建 embedding_cache 表。"""
    op.create_table(
        "embedding_cache",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, primary_key=True, comment="主键"),
        sa.Column("cache_key", sa.String(64), nullable=False, comment="SHA256(text|model|dim)"),
        sa.Column("text_sample", sa.String(200), nullable=True, comment="原文前200字(仅排查用)"),
        sa.Column("model", sa.String(64), nullable=False, comment="embedding模型名"),
        sa.Column("dim", sa.Integer(), nullable=False, comment="向量维度"),
        sa.Column("embedding", mysql.LONGTEXT(), nullable=False, comment="向量本体(JSON字符串,精确往返)"),
        sa.Column("hit_count", mysql.BIGINT(unsigned=True), nullable=False, server_default="0", comment="命中次数"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False, comment="更新时间"),
        sa.UniqueConstraint("cache_key", name="uk_embedding_cache_key"),
        comment="Embedding缓存L3持久层：Redis降级兜底",
        **_TABLE_KW,
    )


def downgrade() -> None:
    """Downgrade schema：删除 embedding_cache 表。"""
    op.drop_table("embedding_cache")
