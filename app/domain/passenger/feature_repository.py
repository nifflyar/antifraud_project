from abc import ABC, abstractmethod

from app.domain.passenger.entity import PassengerFeatures
from app.domain.passenger.vo import PassengerId


class IPassengerFeatureRepository(ABC):

    @abstractmethod
    async def get_by_passenger_id(
        self, passenger_id: PassengerId
    ) -> PassengerFeatures | None: ...

    @abstractmethod
    async def save(
        self, passenger_id: PassengerId, features: PassengerFeatures
    ) -> None: ...

    @abstractmethod
    async def bulk_upsert(
        self, items: list[tuple[PassengerId, PassengerFeatures]]
    ) -> None:
        """Массовое сохранение/обновление признаков — используется ETL-пайплайном."""
        ...

    @abstractmethod
    async def delete_by_passenger_id(self, passenger_id: PassengerId) -> None: ...
