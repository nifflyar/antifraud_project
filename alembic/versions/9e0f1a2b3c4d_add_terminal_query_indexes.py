"""add_terminal_query_indexes

Revision ID: 9e0f1a2b3c4d
Revises: 9d0e1f2a3b4c
Create Date: 2026-06-06 03:30:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = "9e0f1a2b3c4d"
down_revision: Union[str, Sequence[str], None] = "9d0e1f2a3b4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS idx_transactions_terminal_datetime ON transactions (terminal, op_datetime DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_transactions_terminal_type_datetime ON transactions (terminal, op_type, op_datetime DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_transactions_cashdesk_datetime ON transactions (cashdesk, op_datetime DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_transactions_point_of_sale_datetime ON transactions (point_of_sale, op_datetime DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_transactions_aggregator_datetime ON transactions (aggregator, op_datetime DESC)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_transactions_aggregator_datetime")
    op.execute("DROP INDEX IF EXISTS idx_transactions_point_of_sale_datetime")
    op.execute("DROP INDEX IF EXISTS idx_transactions_cashdesk_datetime")
    op.execute("DROP INDEX IF EXISTS idx_transactions_terminal_type_datetime")
    op.execute("DROP INDEX IF EXISTS idx_transactions_terminal_datetime")
