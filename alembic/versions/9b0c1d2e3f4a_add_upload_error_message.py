"""add_upload_error_message

Revision ID: 9b0c1d2e3f4a
Revises: 8c4d5e6f7a8b
Create Date: 2026-06-06 02:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b0c1d2e3f4a"
down_revision: Union[str, Sequence[str], None] = "8c4d5e6f7a8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("uploads", sa.Column("error_message", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    op.drop_column("uploads", "error_message")
