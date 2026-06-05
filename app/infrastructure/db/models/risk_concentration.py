from datetime import datetime

from sqlalchemy import TIMESTAMP, Enum, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.risk.vo import RiskConcentrationId, DimensionType

from .base import BaseORMModel
from .types.entities import RiskConcentrationIdType


class RiskConcentrationModel(BaseORMModel):
    __tablename__ = "risk_concentrations"
    __table_args__ = (
        UniqueConstraint(
            "dimension_type", "dimension_value", name="uq_risk_concentration_dim"
        ),
    )

    id: Mapped[RiskConcentrationId] = mapped_column(
        RiskConcentrationIdType, primary_key=True
    )
    dimension_type: Mapped[DimensionType] = mapped_column(
        Enum(DimensionType, name="dimensiontype", create_type=True),
        nullable=False,
        index=True,
    )
    dimension_value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    total_ops: Mapped[int] = mapped_column(Integer, nullable=False)
    highrisk_ops: Mapped[int] = mapped_column(Integer, nullable=False)
    share_highrisk_ops: Mapped[float] = mapped_column(Float, nullable=False)
    lift_vs_base: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), index=True
    )
