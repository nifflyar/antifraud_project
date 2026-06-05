from datetime import datetime

from sqlalchemy import BIGINT, TIMESTAMP, Boolean, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.passenger.vo import PassengerId

from .base import BaseORMModel
from .types.entities import PassengerIdType


class PassengerFeaturesModel(BaseORMModel):
    """Признаки пассажира, вычисленные в процессе ETL-пайплайна."""

    __tablename__ = "passenger_features"

    passenger_id: Mapped[PassengerId] = mapped_column(
        PassengerIdType,
        ForeignKey("passengers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    total_tickets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    refund_cnt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    refund_share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    night_tickets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    night_share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_tickets_month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_tickets_same_depday: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    refund_close_ratio: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    tickets_per_train_peak: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    fio_fake_score_max: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    late_refunds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    late_refund_share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    very_late_refunds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    very_late_refund_share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quick_refunds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quick_refund_share: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    activity_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    suspicious_refund_pattern_cnt: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    refund_amount_diversity: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0
    )
    seat_blocking_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    calculated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
