from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.transaction.repository import ITransactionRepository
from app.application.common.reports import ExcelReportGenerator

@dataclass
class ExportSuspiciousInput:
    train_no: Optional[str] = None
    cashdesk: Optional[str] = None
    terminal: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class ExportSuspiciousOperationsExcelInteractor:
    def __init__(self, transaction_repo: ITransactionRepository):
        self._transaction_repo = transaction_repo

    async def execute(self, input_dto: ExportSuspiciousInput) -> bytes:
        # Fetch all records without pagination for the report
        transactions_with_risk = await self._transaction_repo.get_suspicious(
            train_no=input_dto.train_no,
            cashdesk=input_dto.cashdesk,
            terminal=input_dto.terminal,
            date_from=input_dto.date_from,
            date_to=input_dto.date_to,
            limit=50000, # Large limit for export
            offset=0
        )

        headers = [
            "ID операции",
            "Тип операции",
            "Дата операции (Астана GMT+5)",
            "Дата отправления (Астана GMT+5)",
            "Пассажир ID",
            "Билет",
            "Заказ",
            "ФИО",
            "Поезд",
            "Маршрут",
            "Канал",
            "Агрегатор",
            "Терминал",
            "Пункт продажи",
            "Тариф",
            "Класс",
            "Сумма, ₸",
            "Уровень риска",
            "Score операции",
            "Причины риска",
        ]
        
        data = []
        for tx, risk_band, operation_score, operation_reasons in transactions_with_risk:
            data.append([
                tx.id.value,
                tx.op_type.value,
                tx.op_datetime,
                tx.dep_datetime,
                tx.passenger_id.value if tx.passenger_id else "",
                tx.ticket_no or "",
                tx.order_no or "",
                tx.fio or "",
                tx.train_no,
                tx.route or "",
                tx.channel,
                tx.aggregator or "",
                tx.terminal or "",
                tx.point_of_sale or tx.cashdesk or "",
                tx.tariff_type or "",
                tx.service_class or "",
                tx.amount,
                risk_band.value.upper(),
                operation_score,
                "; ".join(operation_reasons),
            ])

        generator = ExcelReportGenerator(title="Подозрительные операции")
        generator.write_headers(headers)
        generator.write_rows(data)
        
        return generator.get_file_bytes()
