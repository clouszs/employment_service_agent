"""merge heads b2c3d4e5f6g7 and d32410ec7f9b

Revision ID: 423e571ec022
Revises: b2c3d4e5f6g7, d32410ec7f9b
Create Date: 2026-07-01 10:32:28.965004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = ('b2c34a5b6c7d', 'd32410ec7f9b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
