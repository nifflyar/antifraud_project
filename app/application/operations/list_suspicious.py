from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.transaction.entity import Transaction
from app.domain.transaction.repository import ITransactionRepository
from app.domain.passenger.vo import RiskBand

@dataclass
class ListSuspiciousOperationsInput:
    train_no: Optional[str] = None
    cashdesk: Optional[str] = None
    terminal: Optional[str] = None
    channel: Optional[str] = None
    aggregator: Optional[str] = None
    point_of_sale: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "risk_score"
    sort_order: str = "desc"
    limit: int = 100
    offset: int = 0

@dataclass
class ListOperationsInput:
    train_no: Optional[str] = None
    cashdesk: Optional[str] = None
    terminal: Optional[str] = None
    channel: Optional[str] = None
    aggregator: Optional[str] = None
    point_of_sale: Optional[str] = None
    op_type: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "date"
    sort_order: str = "desc"
    limit: int = 100
    offset: int = 0
    include_risk_stats: bool = False


class ListSuspiciousOperationsInteractor:
    def __init__(self, transaction_repo: ITransactionRepository):
        self._tx_repo = transaction_repo

    async def execute(self, input_dto: ListSuspiciousOperationsInput) -> tuple[list[tuple[Transaction, RiskBand, int, list[str]]], int]:
        results = await self._tx_repo.get_suspicious(
            train_no=input_dto.train_no,
            cashdesk=input_dto.cashdesk,
            terminal=input_dto.terminal,
            channel=input_dto.channel,
            aggregator=input_dto.aggregator,
            point_of_sale=input_dto.point_of_sale,
            date_from=input_dto.date_from,
            date_to=input_dto.date_to,
            sort_by=input_dto.sort_by,
            sort_order=input_dto.sort_order,
            limit=input_dto.limit,
            offset=input_dto.offset
        )
        total = await self._tx_repo.count_suspicious(
            train_no=input_dto.train_no,
            cashdesk=input_dto.cashdesk,
            terminal=input_dto.terminal,
            channel=input_dto.channel,
            aggregator=input_dto.aggregator,
            point_of_sale=input_dto.point_of_sale,
            date_from=input_dto.date_from,
            date_to=input_dto.date_to
        )
        return results, total


class ListOperationsInteractor:
    def __init__(self, transaction_repo: ITransactionRepository):
        self._tx_repo = transaction_repo

    async def execute(self, input_dto: ListOperationsInput) -> tuple[list[tuple[Transaction, RiskBand, int, list[str]]], int, dict[str, int] | None]:
        results = await self._tx_repo.get_operations(
            train_no=input_dto.train_no,
            cashdesk=input_dto.cashdesk,
            terminal=input_dto.terminal,
            channel=input_dto.channel,
            aggregator=input_dto.aggregator,
            point_of_sale=input_dto.point_of_sale,
            op_type=input_dto.op_type,
            search=input_dto.search,
            date_from=input_dto.date_from,
            date_to=input_dto.date_to,
            sort_by=input_dto.sort_by,
            sort_order=input_dto.sort_order,
            limit=input_dto.limit,
            offset=input_dto.offset,
        )
        total = await self._tx_repo.count_operations(
            train_no=input_dto.train_no,
            cashdesk=input_dto.cashdesk,
            terminal=input_dto.terminal,
            channel=input_dto.channel,
            aggregator=input_dto.aggregator,
            point_of_sale=input_dto.point_of_sale,
            op_type=input_dto.op_type,
            search=input_dto.search,
            date_from=input_dto.date_from,
            date_to=input_dto.date_to,
        )
        risk_stats = None
        if input_dto.include_risk_stats:
            risk_stats = await self._tx_repo.get_operation_risk_stats(
                train_no=input_dto.train_no,
                cashdesk=input_dto.cashdesk,
                terminal=input_dto.terminal,
                channel=input_dto.channel,
                aggregator=input_dto.aggregator,
                point_of_sale=input_dto.point_of_sale,
                op_type=input_dto.op_type,
                search=input_dto.search,
                date_from=input_dto.date_from,
                date_to=input_dto.date_to,
            )
        return results, total, risk_stats
