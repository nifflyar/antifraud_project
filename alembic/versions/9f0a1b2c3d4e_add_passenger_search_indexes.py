"""add_passenger_search_indexes

Revision ID: 9f0a1b2c3d4e
Revises: 9e0f1a2b3c4d
Create Date: 2026-06-08 12:00:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = "9f0a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "9e0f1a2b3c4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_CONFUSABLE_SOURCE = "АВЕКМНОРСТУХІ"
_CONFUSABLE_TARGET = "ABEKMHOPCTYXI"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_passengers_fio_clean_trgm "
        "ON passengers USING gin (fio_clean gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_passengers_fio_clean_skeleton_trgm "
        "ON passengers USING gin "
        f"((translate(upper(fio_clean), '{_CONFUSABLE_SOURCE}', '{_CONFUSABLE_TARGET}')) gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_iin_trgm "
        "ON transactions USING gin (iin gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_doc_no_trgm "
        "ON transactions USING gin (doc_no gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_phone_trgm "
        "ON transactions USING gin (phone gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_ticket_no_trgm "
        "ON transactions USING gin (ticket_no gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_order_no_trgm "
        "ON transactions USING gin (order_no gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_transactions_order_no_trgm")
    op.execute("DROP INDEX IF EXISTS idx_transactions_ticket_no_trgm")
    op.execute("DROP INDEX IF EXISTS idx_transactions_phone_trgm")
    op.execute("DROP INDEX IF EXISTS idx_transactions_doc_no_trgm")
    op.execute("DROP INDEX IF EXISTS idx_transactions_iin_trgm")
    op.execute("DROP INDEX IF EXISTS idx_passengers_fio_clean_skeleton_trgm")
    op.execute("DROP INDEX IF EXISTS idx_passengers_fio_clean_trgm")
