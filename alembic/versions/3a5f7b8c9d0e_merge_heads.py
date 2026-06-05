"""Merge migration to reconcile multiple heads

Revision ID: 3a5f7b8c9d0e
Revises: 7cef62923e64, 2f2e5e6d9a7b
Create Date: 2026-05-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a5f7b8c9d0e'
down_revision = ('7cef62923e64', '2f2e5e6d9a7b')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
