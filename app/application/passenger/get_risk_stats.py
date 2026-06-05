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
        critical = await self._repo.count(risk_band=RiskBand.critical, search=search)
        high = await self._repo.count(risk_band=RiskBand.high, search=search)
        medium = await self._repo.count(risk_band=RiskBand.medium, search=search)
        low = await self._repo.count(risk_band=RiskBand.low, search=search)

        # Получить общее количество пассажиров (с фильтром поиска, но БЕЗ фильтра по risk_band)
        total_passengers = await self._repo.count(risk_band=None, search=search)

        # Пассажиры БЕЗ оценок риска
        unscored = total_passengers - (critical + high + medium + low)
        total = total_passengers

        return PassengerRiskStats(
            critical=critical,
            high=high,
            medium=medium,
            low=low,
            unscored=unscored,
            total=total
        )
