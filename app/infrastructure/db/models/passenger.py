from datetime import datetime

from sqlalchemy import TIMESTAMP, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.passenger.vo import PassengerId

from .base import BaseORMModel
from .types.entities import PassengerIdType


class PassengerModel(BaseORMModel):
    """Агрегированный профиль пассажира.

    Признаки и результаты скоринга хранятся в отдельных таблицах:
    - passenger_features (PassengerFeaturesModel)
    - passenger_scores   (PassengerScoreModel)
    """

    __tablename__ = "passengers"

    id: Mapped[PassengerId] = mapped_column(PassengerIdType, primary_key=True)
    fio_clean: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    fake_fio_score: Mapped[float] = mapped_column(Float, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )
