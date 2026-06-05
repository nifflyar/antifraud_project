"""Add passenger_features and passenger_scores tables; drop features/score JSON columns from passengers

Revision ID: a3f2c1b4d5e6
Revises: dcd4f8f82426
Create Date: 2026-04-14 20:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a3f2c1b4d5e6'
down_revision: Union[str, Sequence[str], None] = 'dcd4f8f82426'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Используем TEXT-тип для risk_band — избегаем конфликтов
# с автоматическим before_create событием SQLAlchemy для enum-типов.
RISKBAND_TYPE = sa.String(20)


def upgrade() -> None:
    """Upgrade schema.

    1. Удаляем JSON-колонки features и score из таблицы passengers
       (данные переносятся в отдельные нормализованные таблицы).
    2. Создаём таблицу passenger_features - вычисленные ETL-признаки пассажира.
    3. Создаём enum riskband (IF NOT EXISTS) и таблицу passenger_scores.
    """

    # 1. Удалить JSON-колонки из passengers (IF EXISTS для идемпотентности)
    op.execute(sa.text("ALTER TABLE passengers DROP COLUMN IF EXISTS features"))
    op.execute(sa.text("ALTER TABLE passengers DROP COLUMN IF EXISTS score"))


    # 2. Таблица passenger_features
    op.create_table(
        'passenger_features',
        sa.Column(
            'passenger_id',
            sa.BigInteger(),
            sa.ForeignKey('passengers.id', ondelete='CASCADE'),
            primary_key=True,
            nullable=False,
        ),
        sa.Column('total_tickets',           sa.Integer(), nullable=False, server_default='0'),
        sa.Column('refund_cnt',              sa.Integer(), nullable=False, server_default='0'),
        sa.Column('refund_share',            sa.Float(),   nullable=False, server_default='0'),
        sa.Column('night_tickets',           sa.Integer(), nullable=False, server_default='0'),
        sa.Column('night_share',             sa.Float(),   nullable=False, server_default='0'),
        sa.Column('max_tickets_month',       sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_tickets_same_depday', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('refund_close_ratio',      sa.Float(),   nullable=False, server_default='0'),
        sa.Column('tickets_per_train_peak',  sa.Float(),   nullable=False, server_default='0'),
        sa.Column('fio_fake_score_max',      sa.Float(),   nullable=False, server_default='0'),
        sa.Column('seat_blocking_flag',      sa.Boolean(), nullable=False, server_default='false'),
        sa.Column(
            'calculated_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
    )
    op.create_index(
        'ix_passenger_features_seat_blocking_flag',
        'passenger_features',
        ['seat_blocking_flag'],
    )

    # 3. Enum riskband: создаём через raw DDL только если ещё не существует.
    # НЕ используем sa.Enum() в create_table, чтобы избежать DuplicateObject
    # от автоматического before_create события SQLAlchemy.
    op.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE riskband AS ENUM ('low', 'medium', 'high', 'critical'); "
        "EXCEPTION WHEN duplicate_object THEN null; "
        "END $$"
    ))

    # 4. Таблица passenger_scores
    # risk_band хранится как VARCHAR(20) + CHECK constraint.
    op.create_table(
        'passenger_scores',
        sa.Column(
            'passenger_id',
            sa.BigInteger(),
            sa.ForeignKey('passengers.id', ondelete='CASCADE'),
            primary_key=True,
            nullable=False,
        ),
        sa.Column('rule_score',         sa.Float(),        nullable=False, server_default='0'),
        sa.Column('ml_score',           sa.Float(),        nullable=False, server_default='0'),
        sa.Column('final_score',        sa.Float(),        nullable=False, server_default='0'),
        sa.Column('risk_band',          RISKBAND_TYPE,     nullable=False, server_default='low'),
        sa.Column('top_reasons',        postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('seat_blocking_flag', sa.Boolean(),      nullable=False, server_default='false'),
        sa.Column(
            'scored_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint(
            "risk_band IN ('low', 'medium', 'high', 'critical')",
            name='ck_passenger_scores_risk_band',
        ),
    )
    op.create_index('ix_passenger_scores_final_score',        'passenger_scores', ['final_score'])
    op.create_index('ix_passenger_scores_risk_band',          'passenger_scores', ['risk_band'])
    op.create_index('ix_passenger_scores_seat_blocking_flag', 'passenger_scores', ['seat_blocking_flag'])
    op.create_index('ix_passenger_scores_scored_at',          'passenger_scores', ['scored_at'])


def downgrade() -> None:
    """Downgrade schema.

    1. Удаляем таблицы passenger_scores и passenger_features.
    2. Возвращаем JSON-колонки features и score в таблицу passengers.
    """

    # 1. Удалить новые таблицы
    op.drop_index('ix_passenger_scores_scored_at',          table_name='passenger_scores')
    op.drop_index('ix_passenger_scores_seat_blocking_flag', table_name='passenger_scores')
    op.drop_index('ix_passenger_scores_risk_band',          table_name='passenger_scores')
    op.drop_index('ix_passenger_scores_final_score',        table_name='passenger_scores')
    op.drop_table('passenger_scores')

    op.drop_index('ix_passenger_features_seat_blocking_flag', table_name='passenger_features')
    op.drop_table('passenger_features')

    # 2. Вернуть JSON-колонки в passengers
    with op.batch_alter_table('passengers') as batch_op:
        batch_op.add_column(sa.Column('features', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('score',    sa.JSON(), nullable=True))
