from dataclasses import dataclass
from datetime import datetime


from app.domain.transaction.vo import TransactionId, OperationType
from app.domain.upload.vo import UploadId
from app.domain.passenger.vo import PassengerId


@dataclass
class Transaction:
    id: TransactionId
    upload_id: UploadId
    source: str

    # Operation type: sale or refund
    op_type: OperationType

    # Timestamps
    op_datetime: datetime
    dep_datetime: datetime | None

    # Train info
    train_no: str | None

    # Sale channel info
    channel: str | None
    aggregator: str | None
    terminal: str | None
    cashdesk: str | None
    point_of_sale: str | None

    # Financial info
    amount: float
    fee: float

    # Passenger info
    fio: str | None
    iin: str | None
    doc_no: str | None
    phone: str | None = None
    gender: str | None = None

    # Excel/source attributes used by dashboards and detail tables
    ticket_no: str | None = None
    tariff_type: str | None = None
    service_class: str | None = None
    branch: str | None = None
    sale_user: str | None = None
    carrier: str | None = None
    settlement_type: str | None = None
    order_no: str | None = None
    dep_station: str | None = None
    arr_station: str | None = None
    route: str | None = None
    passenger_id: PassengerId | None = None


    def is_refund(self) -> bool:
        return self.op_type == OperationType.REFUND

    def hours_before_departure(self) -> float | None:
        if self.dep_datetime is None:
            return None
        delta = self.dep_datetime - self.op_datetime
        return delta.total_seconds() / 3600

    def is_last_minute_refund(self, threshold_hours: float = 1.0) -> bool:
        if not self.is_refund():
            return False
        hours = self.hours_before_departure()
        if hours is None:
            return False
        return 0 <= hours <= threshold_hours

    def is_night_operation(self) -> bool:
        hour = self.op_datetime.hour
        return hour >= 23 or hour < 6
