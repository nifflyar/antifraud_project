"""fix_enum_case

Revision ID: 3000198b3bb4
Revises: a3e5c920c19c
Create Date: 2026-04-15 15:11:44.297989

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3000198b3bb4'
down_revision: Union[str, Sequence[str], None] = 'a3e5c920c19c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("COMMIT")
    op.execute("ALTER TYPE operationtype ADD VALUE 'REDEEM'")
    op.execute("ALTER TYPE operationtype ADD VALUE 'OTHER'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
