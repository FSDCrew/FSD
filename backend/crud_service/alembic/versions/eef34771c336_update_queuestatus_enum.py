"""Update

Revision ID: eef34771c336
Revises: cd1452694ffa
Create Date: 2025-12-03 03:16:05.437747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eef34771c336'
down_revision: Union[str, Sequence[str], None] = 'cd1452694ffa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add CANCELLED value to queuestatus enum
    op.execute("ALTER TYPE queuestatus ADD VALUE IF NOT EXISTS 'CANCELLED'")


def downgrade() -> None:
    """Dowgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values directly
    # You would need to recreate the enum type, which is complex
    # For now, we'll leave it as a no-op
    pass
