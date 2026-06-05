from dataclasses import dataclass
from typing import Optional

from app.domain.passenger.repository import IPassengerRepository
from app.domain.passenger.vo import RiskBand
from app.application.common.reports import ExcelReportGenerator


@dataclass
class ExportPassengersByRiskInput:
    risk_band: Optional[RiskBand] = None
    search: Optional[str] = None


class ExportPassengersByRiskExcelInteractor:
    def __init__(self, passenger_repo: IPassengerRepository):
        self._passenger_repo = passenger_repo

    async def execute(self, input_dto: ExportPassengersByRiskInput) -> bytes:
        # Fetch all passengers without pagination for the report
        passengers = await self._passenger_repo.get_all(
            risk_band=input_dto.risk_band,
            search=input_dto.search,
            limit=50000,  # Large limit for export
            offset=0
        )

        headers = [
            "ID Пассажира",
            "ФИО",
            "Риск-зона",
            "Финальный балл",
            "Вероятность поддельного имени",
            "Последний раз видел",
            "Количество билетов",
            "Доля возвратов",
            "Ночные операции %",
        ]

        data = []
        for passenger in passengers:
            if passenger.score:
                risk_band_text = passenger.score.risk_band.value.upper()
                final_score = passenger.score.final_score
            else:
                risk_band_text = "N/A"
                final_score = 0.0

            if passenger.features:
                total_tickets = passenger.features.total_tickets
                refund_share = passenger.features.refund_share * 100
                night_share = passenger.features.night_share * 100 if hasattr(passenger.features, 'night_share') else 0
            else:
                total_tickets = 0
                refund_share = 0.0
                night_share = 0.0

            data.append([
                passenger.id.value,
                passenger.fio_clean,
                risk_band_text,
                round(final_score, 2),
                round(passenger.fake_fio_score * 100, 2),
                passenger.last_seen_at.isoformat() if passenger.last_seen_at else "",
                total_tickets,
                round(refund_share, 2),
                round(night_share, 2),
            ])

        title = f"Пассажиры - {input_dto.risk_band.value.upper() if input_dto.risk_band else 'ВСЕ'}"
        generator = ExcelReportGenerator(title=title)
        generator.write_headers(headers)
        generator.write_rows(data)

        return generator.get_file_bytes()
