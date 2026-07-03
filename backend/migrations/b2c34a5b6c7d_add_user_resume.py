"""add_user_resume: 新增 user_resume 表，保存学生生成的简历 JSON + PDF 路径。"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b2c34a5b6c7d"
down_revision: str = "87dc2a1b3c4e"
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


def upgrade() -> None:
    op.create_table(
        "user_resume",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="简历ID"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="所属用户ID"),
        sa.Column("title", sa.String(128), nullable=False, comment="简历标题"),
        sa.Column("content", sa.Text(), nullable=False, comment="简历JSON原文"),
        sa.Column("pdf_path", sa.String(512), nullable=True, comment="PDF文件路径"),
        sa.Column("is_default", sa.Integer(), server_default="0", nullable=False, comment="是否默认简历"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_resume_user_id", "user_resume", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_resume_user_id", table_name="user_resume")
    op.drop_table("user_resume")
