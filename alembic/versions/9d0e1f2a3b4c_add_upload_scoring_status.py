"""add_upload_scoring_status

Revision ID: 9d0e1f2a3b4c
Revises: 9c0d1e2f3a4b
Create Date: 2026-06-06 03:05:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = "9d0e1f2a3b4c"
down_revision: Union[str, Sequence[str], None] = "9c0d1e2f3a4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE uploadstatus ADD VALUE IF NOT EXISTS 'SCORING'")
    op.execute("ALTER TYPE uploadstatus ADD VALUE IF NOT EXISTS 'scoring'")


def downgrade() -> None:
    pass
