"""ensure_lowercase_operation_types

Revision ID: 9c0d1e2f3a4b
Revises: 9b0c1d2e3f4a
Create Date: 2026-06-06 02:45:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = "9c0d1e2f3a4b"
down_revision: Union[str, Sequence[str], None] = "9b0c1d2e3f4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE operationtype ADD VALUE IF NOT EXISTS 'sale'")
    op.execute("ALTER TYPE operationtype ADD VALUE IF NOT EXISTS 'refund'")
    op.execute("ALTER TYPE operationtype ADD VALUE IF NOT EXISTS 'redeem'")
    op.execute("ALTER TYPE operationtype ADD VALUE IF NOT EXISTS 'other'")


def downgrade() -> None:
    pass
