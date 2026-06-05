"""fix_risk_band_type

Revision ID: a9fedb4eb37d
Revises: 0455d06f842b
Create Date: 2026-04-17 17:44:46.434407

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9fedb4eb37d'
down_revision: Union[str, Sequence[str], None] = '0455d06f842b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to use native ENUM for risk_band."""
    # 1. Drop the check constraint
    op.execute("ALTER TABLE passenger_scores DROP CONSTRAINT IF EXISTS ck_passenger_scores_risk_band")
    
    # 2. Drop the existing default to avoid type cast issues
    op.execute("ALTER TABLE passenger_scores ALTER COLUMN risk_band DROP DEFAULT")
    
    # 3. Change column type to riskband enum
    op.execute("ALTER TABLE passenger_scores ALTER COLUMN risk_band TYPE riskband USING risk_band::riskband")
    
    # 4. Set the new default
    op.execute("ALTER TABLE passenger_scores ALTER COLUMN risk_band SET DEFAULT 'low'::riskband")


def downgrade() -> None:
    """Downgrade schema back to VARCHAR."""
    op.execute("ALTER TABLE passenger_scores ALTER COLUMN risk_band DROP DEFAULT")
    op.execute("ALTER TABLE passenger_scores ALTER COLUMN risk_band TYPE VARCHAR(20) USING risk_band::VARCHAR")
    op.execute("ALTER TABLE passenger_scores ALTER COLUMN risk_band SET DEFAULT 'low'")
    op.create_check_constraint(
        'ck_passenger_scores_risk_band',
        'passenger_scores',
        sa.column('risk_band').in_(['low', 'medium', 'high', 'critical'])
    )
