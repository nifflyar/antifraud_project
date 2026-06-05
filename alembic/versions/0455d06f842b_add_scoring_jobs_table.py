"""add_scoring_jobs_table

Revision ID: 0455d06f842b
Revises: 3000198b3bb4
Create Date: 2026-04-17 17:35:42.576508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0455d06f842b'
down_revision: Union[str, Sequence[str], None] = '3000198b3bb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('scoring_jobs',
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('upload_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['upload_id'], ['uploads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('job_id')
    )
    op.create_index(op.f('ix_scoring_jobs_status'), 'scoring_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_scoring_jobs_upload_id'), 'scoring_jobs', ['upload_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_scoring_jobs_upload_id'), table_name='scoring_jobs')
    op.drop_index(op.f('ix_scoring_jobs_status'), table_name='scoring_jobs')
    op.drop_table('scoring_jobs')
