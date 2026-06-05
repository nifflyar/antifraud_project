from abc import ABC, abstractmethod

from app.domain.passenger.entity import PassengerScore
from app.domain.passenger.vo import PassengerId, RiskBand


class IPassengerScoreRepository(ABC):

    @abstractmethod
    async def get_by_passenger_id(
        self, passenger_id: PassengerId
    ) -> PassengerScore | None: ...

    @abstractmethod
    async def save(
        self, passenger_id: PassengerId, score: PassengerScore
    ) -> None: ...

    @abstractmethod
    async def bulk_upsert(
        self, items: list[tuple[PassengerId, PassengerScore]]
    ) -> None:
        """Массовое сохранение/обновление скоров — вызывается после ML-скоринга."""
        ...

    @abstractmethod
    async def count_by_risk_band(self, risk_band: RiskBand) -> int: ...

    @abstractmethod
    async def delete_by_passenger_id(self, passenger_id: PassengerId) -> None: ...
