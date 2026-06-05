from datetime import datetime

from sqlalchemy import TIMESTAMP, Enum, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.transaction.vo import TransactionId, OperationType
from app.domain.upload.vo import UploadId
from app.domain.passenger.vo import PassengerId

from .base import BaseORMModel
from .types.entities import (
    TransactionIdType,
    UploadIdType,
    PassengerIdType,
)


class TransactionModel(BaseORMModel):
    __tablename__ = "transactions"

    id: Mapped[TransactionId] = mapped_column(TransactionIdType, primary_key=True)
    upload_id: Mapped[UploadId] = mapped_column(UploadIdType, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    op_type: Mapped[OperationType] = mapped_column(
        Enum(
            OperationType,
            name="operationtype",
            create_type=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        index=True,
    )
    op_datetime: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )
    dep_datetime: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    train_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    aggregator: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    terminal: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    cashdesk: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    point_of_sale: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    fee: Mapped[float] = mapped_column(Float, nullable=False)
    fio: Mapped[str | None] = mapped_column(String(255), nullable=True)
    iin: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    doc_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    ticket_no: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    tariff_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    service_class: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    branch: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    sale_user: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    carrier: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    settlement_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    order_no: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    dep_station: Mapped[str | None] = mapped_column(String(255), nullable=True)
    arr_station: Mapped[str | None] = mapped_column(String(255), nullable=True)
    route: Mapped[str | None] = mapped_column(String(512), nullable=True)
    passenger_id: Mapped[PassengerId | None] = mapped_column(
        PassengerIdType, nullable=True, index=True
    )
