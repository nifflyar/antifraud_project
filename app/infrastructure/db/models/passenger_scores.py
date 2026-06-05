from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.domain.passenger.vo import PassengerId, RiskBand

from .base import BaseORMModel
from .types.entities import PassengerIdType


class PassengerScoreModel(BaseORMModel):
    """Результаты скоринга пассажира, заполняются ML-сервисом.

    Enum riskband создаётся миграцией через DO/EXCEPTION блок.
    В модели используем create_type=False чтобы SQLAlchemy
    не пытался создать тип повторно при инициализации.
    """

    __tablename__ = "passenger_scores"

    passenger_id: Mapped[PassengerId] = mapped_column(
        PassengerIdType,
        ForeignKey("passengers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    rule_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ml_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    final_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, index=True
    )
    # create_type=False: тип riskband создаётся миграцией вручную (DO/EXCEPTION),
    # чтобы избежать ошибки "type already exists" при повторном запуске.
    risk_band: Mapped[RiskBand] = mapped_column(
        Enum(RiskBand, name="riskband", create_type=False),
        nullable=False,
        default=RiskBand.low,
        index=True,
    )
    top_reasons: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    seat_blocking_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    is_manual: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    scored_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True
    )
