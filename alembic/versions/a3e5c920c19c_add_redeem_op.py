"""add_redeem_op

Revision ID: a3e5c920c19c
Revises: a3f2c1b4d5e6
Create Date: 2026-04-15 15:00:41.477852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3e5c920c19c'
down_revision: Union[str, Sequence[str], None] = 'a3f2c1b4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use raw connection to execute outside of transaction for PostgreSQL ENUM
    op.execute("COMMIT")
    op.execute("ALTER TYPE operationtype ADD VALUE 'redeem'")
    op.execute("ALTER TYPE operationtype ADD VALUE 'other'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: Logic to remove values from ENUM in Postgres is complex (requires dropping/recreating type)
    # For this project, we accept that ENUM values are only added.
    pass
