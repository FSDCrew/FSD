"""update_uuid_defaults

Revision ID: update_uuid_defaults
Revises: 20ac7846080d
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'update_uuid_defaults'
down_revision: Union[str, Sequence[str], None] = '20ac7846080d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Update UUID columns to use gen_random_uuid() as default."""
    op.execute("ALTER TABLE users ALTER COLUMN id SET DEFAULT gen_random_uuid()")
    op.execute("ALTER TABLE crews ALTER COLUMN id SET DEFAULT gen_random_uuid()")
    op.execute("ALTER TABLE tasks ALTER COLUMN id SET DEFAULT gen_random_uuid()")
    op.execute("ALTER TABLE crew_runs ALTER COLUMN id SET DEFAULT gen_random_uuid()")
    op.execute("ALTER TABLE artifacts ALTER COLUMN id SET DEFAULT gen_random_uuid()")

def downgrade() -> None:
    """Remove UUID defaults."""
    op.execute("ALTER TABLE users ALTER COLUMN id DROP DEFAULT")
    op.execute("ALTER TABLE crews ALTER COLUMN id DROP DEFAULT")
    op.execute("ALTER TABLE tasks ALTER COLUMN id DROP DEFAULT")
    op.execute("ALTER TABLE crew_runs ALTER COLUMN id DROP DEFAULT")
    op.execute("ALTER TABLE artifacts ALTER COLUMN id DROP DEFAULT")
