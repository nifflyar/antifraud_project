"""Add enhanced refund features to passenger_features table

Revision ID: 2f2e5e6d9a7b
Revises: dd8e2383f024
Create Date: 2026-05-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f2e5e6d9a7b'
down_revision = 'dd8e2383f024'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('passenger_features', sa.Column('late_refunds', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('passenger_features', sa.Column('late_refund_share', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('passenger_features', sa.Column('very_late_refunds', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('passenger_features', sa.Column('very_late_refund_share', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('passenger_features', sa.Column('quick_refunds', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('passenger_features', sa.Column('quick_refund_share', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('passenger_features', sa.Column('activity_days', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('passenger_features', 'activity_days')
    op.drop_column('passenger_features', 'quick_refund_share')
    op.drop_column('passenger_features', 'quick_refunds')
    op.drop_column('passenger_features', 'very_late_refund_share')
    op.drop_column('passenger_features', 'very_late_refunds')
    op.drop_column('passenger_features', 'late_refund_share')
    op.drop_column('passenger_features', 'late_refunds')
