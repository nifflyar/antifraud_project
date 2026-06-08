from dataclasses import dataclass
from app.domain.passenger.repository import IPassengerRepository
from app.domain.passenger.vo import RiskBand

@dataclass
class PassengerRiskStats:
    critical: int
    high: int
    medium: int
    low: int
    unscored: int
    total: int

class GetPassengerRiskStatsInteractor:
    def __init__(self, repository: IPassengerRepository) -> None:
        self._repo = repository

    async def execute(self, search: str | None = None) -> PassengerRiskStats:
        counts = await self._repo.count_risk_bands(search=search)

        return PassengerRiskStats(
            critical=counts.get(RiskBand.critical.value, 0),
            high=counts.get(RiskBand.high.value, 0),
            medium=counts.get(RiskBand.medium.value, 0),
            low=counts.get(RiskBand.low.value, 0),
            unscored=counts.get("unscored", 0),
            total=counts.get("total", 0),
        )
