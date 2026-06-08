# app/domain/passenger/repository.py
from abc import ABC, abstractmethod
from app.domain.passenger.entity import Passenger
from app.domain.passenger.vo import PassengerId, RiskBand

class IPassengerRepository(ABC):

    @abstractmethod
    async def get_by_id(self, passenger_id: PassengerId) -> Passenger | None: ...

    @abstractmethod
    async def get_all(
        self,
        risk_band: RiskBand | None = None,
        search: str | None = None,
        sort_by: str = "risk_band",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Passenger]: ...

    @abstractmethod
    async def count(self, risk_band: RiskBand | None = None, search: str | None = None) -> int: ...

    @abstractmethod
    async def count_risk_bands(self, search: str | None = None) -> dict[str, int]: ...

    @abstractmethod
    async def create_passenger(self, passenger: Passenger) -> None: ...

    @abstractmethod
    async def update_passenger(self, passenger: Passenger) -> None: ...

    @abstractmethod
    async def delete_passenger(self, passenger_id: PassengerId) -> None: ...
