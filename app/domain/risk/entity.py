from dataclasses import dataclass
from datetime import datetime, UTC
from app.domain.risk.vo import DimensionType, RiskConcentrationId

@dataclass
class RiskConcentration:

    id: RiskConcentrationId
    dimension_type: DimensionType
    dimension_value: str

    total_ops: int
    highrisk_ops: int
    share_highrisk_ops: float
    lift_vs_base: float
    calculated_at: datetime

    def is_hotspot(self, lift_threshold: float = 2.0) -> bool:
        return self.lift_vs_base >= lift_threshold

    def risk_label(self) -> str:
        if self.lift_vs_base >= 3.0:
            return "critical_hotspot"
        if self.lift_vs_base >= 2.0:
            return "hotspot"
        if self.lift_vs_base >= 1.5:
            return "elevated"
        return "normal"

    @classmethod
    def create(
        cls,
        concentration_id: int,
        dimension_type: DimensionType,
        dimension_value: str,
        total_ops: int,
        highrisk_ops: int,
        base_share: float,
    ) -> "RiskConcentration":
        share = highrisk_ops / total_ops if total_ops > 0 else 0.0
        lift = share / base_share if base_share > 0 else 1.0
        return cls(
            id=RiskConcentrationId(concentration_id),
            dimension_type=dimension_type,
            dimension_value=dimension_value,
            total_ops=total_ops,
            highrisk_ops=highrisk_ops,
            share_highrisk_ops=share,
            lift_vs_base=lift,
            calculated_at=datetime.now(UTC),
        )