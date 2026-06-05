"""Add suspicious refund pattern detection features."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f1e2a3b4c5d"
down_revision = "3a5f7b8c9d0e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to passenger_features table
    op.add_column(
        "passenger_features",
        sa.Column("suspicious_refund_pattern_cnt", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "passenger_features",
        sa.Column("refund_amount_diversity", sa.Float(), nullable=False, server_default="1.0"),
    )


def downgrade() -> None:
    # Remove columns
    op.drop_column("passenger_features", "refund_amount_diversity")
    op.drop_column("passenger_features", "suspicious_refund_pattern_cnt")
