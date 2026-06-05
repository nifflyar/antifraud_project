"""Add composite indexes for performance optimization.

Revision ID: 001
Revises:
Create Date: 2026-05-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite indexes to core fraud detection tables."""

    # TransactionModel composite indexes
    op.create_index(
        "idx_transaction_upload_datetime",
        "transactions",
        ["upload_id", sa.text("op_datetime DESC")],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_transaction_passenger_datetime",
        "transactions",
        ["passenger_id", sa.text("op_datetime DESC")],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_transaction_type_datetime",
        "transactions",
        ["op_type", sa.text("op_datetime DESC")],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_transaction_channel_datetime",
        "transactions",
        ["channel", sa.text("op_datetime DESC")],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_transaction_type_amount",
        "transactions",
        ["op_type", sa.text("amount DESC")],
        postgresql_using="btree",
    )

    # PassengerScoreModel composite indexes
    op.create_index(
        "idx_score_risk_datetime",
        "passenger_scores",
        ["risk_band", sa.text("scored_at DESC")],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_score_final_datetime",
        "passenger_scores",
        ["final_score", sa.text("scored_at DESC")],
        postgresql_using="btree",
    )

    # PassengerFeaturesModel composite index
    op.create_index(
        "idx_features_passenger_refund",
        "passenger_features",
        ["passenger_id", sa.text("refund_share DESC")],
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Drop all added composite indexes."""
    op.drop_index("idx_features_passenger_refund", table_name="passenger_features")
    op.drop_index("idx_score_final_datetime", table_name="passenger_scores")
    op.drop_index("idx_score_risk_datetime", table_name="passenger_scores")
    op.drop_index("idx_transaction_type_amount", table_name="transactions")
    op.drop_index("idx_transaction_channel_datetime", table_name="transactions")
    op.drop_index("idx_transaction_type_datetime", table_name="transactions")
    op.drop_index("idx_transaction_passenger_datetime", table_name="transactions")
    op.drop_index("idx_transaction_upload_datetime", table_name="transactions")
