"""add_faq_ask_count: kb_faq 增加 ask_count 字段，用于统计学生模糊命中次数。"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


# 识别依赖迁移基线，确保执行顺序正确
revision: str = "87dc2a1b3c4e"
down_revision: str = "fd8202321cd1"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


def upgrade() -> None:
    op.add_column(
        "kb_faq",
        sa.Column(
            "ask_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="模糊命中次数（学生侧）",
        ),
    )
    op.create_index(
        "ix_kb_faq_ask_count",
        "kb_faq",
        ["ask_count"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_kb_faq_ask_count", table_name="kb_faq")
    op.drop_column("kb_faq", "ask_count")
