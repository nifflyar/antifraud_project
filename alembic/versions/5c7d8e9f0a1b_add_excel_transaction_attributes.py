"""add_excel_transaction_attributes

Revision ID: 5c7d8e9f0a1b
Revises: 9f1e2a3b4c5d
Create Date: 2026-05-18 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5c7d8e9f0a1b"
down_revision: Union[str, Sequence[str], None] = "9f1e2a3b4c5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("phone", sa.String(length=50), nullable=True))
    op.add_column("transactions", sa.Column("gender", sa.String(length=20), nullable=True))
    op.add_column("transactions", sa.Column("ticket_no", sa.String(length=50), nullable=True))
    op.add_column("transactions", sa.Column("tariff_type", sa.String(length=100), nullable=True))
    op.add_column("transactions", sa.Column("service_class", sa.String(length=100), nullable=True))
    op.add_column("transactions", sa.Column("branch", sa.String(length=150), nullable=True))
    op.add_column("transactions", sa.Column("sale_user", sa.String(length=150), nullable=True))
    op.add_column("transactions", sa.Column("carrier", sa.String(length=150), nullable=True))
    op.add_column("transactions", sa.Column("settlement_type", sa.String(length=100), nullable=True))

    op.create_index(op.f("ix_transactions_phone"), "transactions", ["phone"], unique=False)
    op.create_index(op.f("ix_transactions_gender"), "transactions", ["gender"], unique=False)
    op.create_index(op.f("ix_transactions_ticket_no"), "transactions", ["ticket_no"], unique=False)
    op.create_index(op.f("ix_transactions_tariff_type"), "transactions", ["tariff_type"], unique=False)
    op.create_index(op.f("ix_transactions_service_class"), "transactions", ["service_class"], unique=False)
    op.create_index(op.f("ix_transactions_branch"), "transactions", ["branch"], unique=False)
    op.create_index(op.f("ix_transactions_sale_user"), "transactions", ["sale_user"], unique=False)
    op.create_index(op.f("ix_transactions_carrier"), "transactions", ["carrier"], unique=False)
    op.create_index(op.f("ix_transactions_settlement_type"), "transactions", ["settlement_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_settlement_type"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_carrier"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_sale_user"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_branch"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_service_class"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_tariff_type"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_ticket_no"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_gender"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_phone"), table_name="transactions")

    op.drop_column("transactions", "settlement_type")
    op.drop_column("transactions", "carrier")
    op.drop_column("transactions", "sale_user")
    op.drop_column("transactions", "branch")
    op.drop_column("transactions", "service_class")
    op.drop_column("transactions", "tariff_type")
    op.drop_column("transactions", "ticket_no")
    op.drop_column("transactions", "gender")
    op.drop_column("transactions", "phone")
