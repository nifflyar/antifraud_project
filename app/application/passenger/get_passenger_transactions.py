from dataclasses import dataclass

from app.domain.transaction.repository import ITransactionRepository
from app.domain.transaction.entity import Transaction
from app.domain.passenger.vo import PassengerId


@dataclass
class PassengerTransactionsResult:
    items: list[Transaction]
    total: int
    limit: int
    offset: int


class GetPassengerTransactionsInteractor:
    def __init__(self, repository: ITransactionRepository) -> None:
        self._repo = repository

    async def execute(
        self, 
        passenger_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> PassengerTransactionsResult:
        pid = PassengerId(passenger_id)
        items = await self._repo.get_by_passenger_id(
            pid,
            limit=limit,
            offset=offset,
        )
        total = await self._repo.count_by_passenger_id(pid)
        return PassengerTransactionsResult(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
