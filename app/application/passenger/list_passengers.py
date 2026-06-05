from dataclasses import dataclass
from app.domain.passenger.repository import IPassengerRepository
from app.domain.passenger.entity import Passenger
from app.domain.passenger.vo import RiskBand

@dataclass
class ListPassengersResult:
    items: list[Passenger]
    total: int
    limit: int
    offset: int

class ListPassengersInteractor:
    def __init__(self, repository: IPassengerRepository) -> None:
        self._repo = repository

    async def execute(
        self,
        risk_band: RiskBand | None = None,
        search: str | None = None,
        sort_by: str = "risk_band",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> ListPassengersResult:
        items = await self._repo.get_all(
            risk_band=risk_band,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        total = await self._repo.count(risk_band=risk_band, search=search)

        return ListPassengersResult(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )
