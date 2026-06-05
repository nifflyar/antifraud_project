"""add_station_and_order_fields

Revision ID: 42bccdaceb52
Revises: dd8e2383f024
Create Date: 2026-04-17 18:35:38

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '42bccdaceb52'
down_revision: Union[str, Sequence[str], None] = 'dd8e2383f024'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('transactions', sa.Column('order_no', sa.String(length=50), nullable=True))
    op.add_column('transactions', sa.Column('dep_station', sa.String(length=100), nullable=True))
    op.add_column('transactions', sa.Column('arr_station', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_transactions_order_no'), 'transactions', ['order_no'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_transactions_order_no'), table_name='transactions')
    op.drop_column('transactions', 'arr_station')
    op.drop_column('transactions', 'dep_station')
    op.drop_column('transactions', 'order_no')
