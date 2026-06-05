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
            "ID Транзакции", 
            "Тип", 
            "Дата операции", 
            "Дата отправления", 
            "Поезд", 
            "Сумма", 
            "Канал", 
            "Маршрут", 
            "Пассажир (ФИО)", 
            "Риск-зона",
            "Оценка операции",
            "Причины"
        ]
        
        data = []
        for tx, risk_band, operation_score, operation_reasons in transactions_with_risk:
            data.append([
                tx.id.value,
                tx.op_type.value,
                tx.op_datetime,
                tx.dep_datetime,
                tx.train_no,
                tx.amount,
                tx.channel,
                tx.route,
                tx.fio,
                risk_band.value.upper(),
                operation_score,
                "; ".join(operation_reasons),
            ])

        generator = ExcelReportGenerator(title="Подозрительные трансзакции")
        generator.write_headers(headers)
        generator.write_rows(data)
        
        return generator.get_file_bytes()
