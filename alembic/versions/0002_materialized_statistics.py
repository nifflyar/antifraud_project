"""Migration: Create materialized statistics tables for instant queries

Revision ID: 1a2b3c4d5e6f
Revises: 5c7d8e9f0a1b
Create Date: 2026-05-22 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "5c7d8e9f0a1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create materialized statistics tables"""

    # Passenger statistics table
    op.create_table(
        'passenger_statistics',
        sa.Column('id', sa.String(50), primary_key=True, server_default='current'),
        sa.Column('total_passengers', sa.Integer, default=0),
        sa.Column('critical_risk_count', sa.Integer, default=0),
        sa.Column('high_risk_count', sa.Integer, default=0),
        sa.Column('medium_risk_count', sa.Integer, default=0),
        sa.Column('low_risk_count', sa.Integer, default=0),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Index('idx_passenger_stats_updated', 'updated_at'),
    )

    # Transaction statistics table
    op.create_table(
        'transaction_statistics',
        sa.Column('id', sa.String(50), primary_key=True, server_default='current'),
        sa.Column('total_operations', sa.Integer, default=0),
        sa.Column('suspicious_operations', sa.Integer, default=0),
        sa.Column('refund_operations', sa.Integer, default=0),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Index('idx_transaction_stats_updated', 'updated_at'),
    )

    # Add composite indexes on frequently-joined columns
    op.create_index(
        'idx_passenger_scores_passenger_risk',
        'passenger_scores',
        ['passenger_id', 'risk_band'],
        postgresql_where=sa.text("risk_band IS NOT NULL")
    )

    op.create_index(
        'idx_transactions_passenger_type',
        'transactions',
        ['passenger_id', 'op_type'],
        postgresql_where=sa.text("passenger_id IS NOT NULL")
    )

    # Covering indexes (include commonly selected columns)
    op.create_index(
        'idx_passengers_fio_covering',
        'passengers',
        ['fio_clean', 'last_seen_at'],
        postgresql_include=['fake_fio_score']
    )


def downgrade() -> None:
    """Drop materialized statistics tables"""
    op.drop_table('transaction_statistics')
    op.drop_table('passenger_statistics')
    op.drop_index('idx_passenger_scores_passenger_risk')
    op.drop_index('idx_transactions_passenger_type')
    op.drop_index('idx_passengers_fio_covering')
