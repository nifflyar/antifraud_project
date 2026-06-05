"""add_unique_risk_concentration

Revision ID: dd8e2383f024
Revises: a9fedb4eb37d
Create Date: 2026-04-17 17:57:16.434407

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd8e2383f024'
down_revision: Union[str, Sequence[str], None] = 'a9fedb4eb37d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Clear old placeholder data to avoid constraint violations
    op.execute("DELETE FROM risk_concentrations")
    
    # 2. Add unique constraint on (dimension_type, dimension_value)
    # This allows us to use on_conflict_do_update on these dimensions instead of ID
    op.create_unique_constraint(
        'uq_risk_concentration_dim',
        'risk_concentrations',
        ['dimension_type', 'dimension_value']
    )


def downgrade() -> None:
    op.drop_constraint('uq_risk_concentration_dim', 'risk_concentrations', type_='unique')
