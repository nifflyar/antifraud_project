"""Add investigation workflow table.

Revision ID: 8c4d5e6f7a8b
Revises: 7a3b5c8d9e0f
Create Date: 2026-05-28 23:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c4d5e6f7a8b"
down_revision: Union[str, Sequence[str], None] = "7a3b5c8d9e0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("passenger_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("priority", sa.String(length=16), nullable=True),
        sa.Column("assignee_user_id", sa.BigInteger(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("updated_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("last_reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("closed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["passenger_id"], ["passengers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("passenger_id", name="uq_investigations_passenger_id"),
    )
    op.create_index("ix_investigations_passenger_id", "investigations", ["passenger_id"])
    op.create_index("ix_investigations_status", "investigations", ["status"])
    op.create_index("ix_investigations_priority", "investigations", ["priority"])
    op.create_index("ix_investigations_assignee_user_id", "investigations", ["assignee_user_id"])
    op.create_index("idx_investigations_status_priority", "investigations", ["status", "priority"])
    op.create_index("idx_investigations_assignee_status", "investigations", ["assignee_user_id", "status"])
    op.create_index("idx_investigations_updated_at", "investigations", ["updated_at"])


def downgrade() -> None:
    op.drop_index("idx_investigations_updated_at", table_name="investigations")
    op.drop_index("idx_investigations_assignee_status", table_name="investigations")
    op.drop_index("idx_investigations_status_priority", table_name="investigations")
    op.drop_index("ix_investigations_assignee_user_id", table_name="investigations")
    op.drop_index("ix_investigations_priority", table_name="investigations")
    op.drop_index("ix_investigations_status", table_name="investigations")
    op.drop_index("ix_investigations_passenger_id", table_name="investigations")
    op.drop_table("investigations")
