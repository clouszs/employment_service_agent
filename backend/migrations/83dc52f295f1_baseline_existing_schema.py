"""baseline existing schema

基线迁移（空迁移）。

作用：标记数据库中已存在的 17 张业务表（sys_/kb_/qa_/op_）为 Alembic 管理基线。
这些表是项目早期手工/脚本建立的，并非由 Alembic 创建，因此本迁移不执行任何 DDL，
仅通过 `alembic stamp` 把数据库版本指针落到这里，作为后续所有迁移的起点。

后续阶段（如阶段 0 的监控表）以本基线为 down_revision 向上叠加。

Revision ID: 83dc52f295f1
Revises:
Create Date: 2026-06-23 21:03:05.090747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83dc52f295f1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
