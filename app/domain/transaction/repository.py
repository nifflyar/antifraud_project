from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.transaction.entity import Transaction
from app.domain.transaction.vo import TransactionId
from app.domain.upload.vo import UploadId
from app.domain.passenger.vo import PassengerId, RiskBand


class ITransactionRepository(ABC):

    @abstractmethod
    async def get_by_id(self, transaction_id: TransactionId) -> Transaction | None: ...

    @abstractmethod
    async def get_all_by_upload_id(
        self, upload_id: UploadId, limit: int = 500, offset: int = 0
    ) -> list[Transaction]: ...

    @abstractmethod
    async def get_by_passenger_id(
        self, passenger_id: PassengerId, limit: int = 100, offset: int = 0
    ) -> list[Transaction]: ...

    @abstractmethod
    async def count_by_passenger_id(self, passenger_id: PassengerId) -> int: ...

    @abstractmethod
    async def get_suspicious(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "risk_score",
        sort_order: str = "desc",
    ) -> list[tuple[Transaction, RiskBand, int, list[str]]]:
        """Операции, у которых есть собственные подозрительные признаки."""
        ...

    @abstractmethod
    async def get_operations(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        op_type: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> list[tuple[Transaction, RiskBand, int, list[str]]]:
        """Все операции с рассчитанным operation-level risk для отображения."""
        ...

    @abstractmethod
    async def count_suspicious(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int: ...

    @abstractmethod
    async def count_scored_suspicious(self) -> int: ...

    @abstractmethod
    async def count_operations(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        op_type: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int: ...

    @abstractmethod
    async def get_operation_risk_stats(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        op_type: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, int]: ...

    @abstractmethod
    async def count_all(self) -> int: ...

    @abstractmethod
    async def create_batch(self, transactions: list[Transaction]) -> None:
        """Bulk insert транзакций — используется ETL-пайплайном."""
        ...

    @abstractmethod
    async def get_risk_trend(
        self, date_from: datetime | None = None, date_to: datetime | None = None
    ) -> list[dict]:
        """Возвращает статистику по дням: дата, общее кол-во, подозрительные."""
        ...

    @abstractmethod
    async def get_dimension_stats(self, dimension_column: str) -> list[dict]: ...

    @abstractmethod
    async def get_dimension_stats_by_passenger_score(self, dimension_column: str) -> list[dict]: ...

    @abstractmethod
    async def get_live_dimension_stats(self, dimension_column: str) -> list[dict]: ...
