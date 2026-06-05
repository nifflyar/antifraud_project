from typing import Optional
from app.domain.passenger.repository import IPassengerRepository
from app.domain.passenger.entity import Passenger
from app.domain.passenger.vo import PassengerId

class GetPassengerProfileInteractor:
    def __init__(self, repository: IPassengerRepository) -> None:
        self._repo = repository

    async def execute(self, passenger_id: int) -> Optional[Passenger]:
        return await self._repo.get_by_id(PassengerId(passenger_id))
