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
            "Уровень риска",
            "Финальный балл",
            "Rule Score",
            "ML Score",
            "Вероятность подозрительного ФИО, %",
            "Первая активность",
            "Последняя активность",
            "Количество билетов",
            "Возвратов",
            "Доля возвратов",
            "Поздние возвраты <6ч",
            "Быстрые возвраты <1ч",
            "Похожие возвраты за день",
            "Ночные операции %",
            "Дней активности",
            "Seat-blocking",
            "Причины риска",
        ]

        data = []
        for passenger in passengers:
            if passenger.score:
                risk_band_text = passenger.score.risk_band.value.upper()
                final_score = passenger.score.final_score
                rule_score = passenger.score.rule_score
                ml_score = passenger.score.ml_score
                seat_blocking = "Да" if passenger.score.seat_blocking_flag else "Нет"
                reasons = "; ".join(passenger.score.top_reasons or [])
            else:
                risk_band_text = "N/A"
                final_score = 0.0
                rule_score = 0.0
                ml_score = 0.0
                seat_blocking = "Нет"
                reasons = ""

            if passenger.features:
                total_tickets = passenger.features.total_tickets
                refund_cnt = passenger.features.refund_cnt
                refund_share = passenger.features.refund_share * 100
                night_share = passenger.features.night_share * 100 if hasattr(passenger.features, 'night_share') else 0
                very_late_refunds = passenger.features.very_late_refunds or 0
                quick_refunds = passenger.features.quick_refunds or 0
                suspicious_refunds = passenger.features.suspicious_refund_pattern_cnt or 0
                activity_days = passenger.features.activity_days or 0
            else:
                total_tickets = 0
                refund_cnt = 0
                refund_share = 0.0
                night_share = 0.0
                very_late_refunds = 0
                quick_refunds = 0
                suspicious_refunds = 0
                activity_days = 0

            data.append([
                passenger.id.value,
                passenger.fio_clean,
                risk_band_text,
                round(final_score, 2),
                round(rule_score, 2),
                round(ml_score, 2),
                round(passenger.fake_fio_score * 100, 2),
                passenger.first_seen_at,
                passenger.last_seen_at,
                total_tickets,
                refund_cnt,
                round(refund_share, 2),
                very_late_refunds,
                quick_refunds,
                suspicious_refunds,
                round(night_share, 2),
                activity_days,
                seat_blocking,
                reasons,
            ])

        title = f"Пассажиры - {input_dto.risk_band.value.upper() if input_dto.risk_band else 'ВСЕ'}"
        generator = ExcelReportGenerator(title=title)
        generator.write_headers(headers)
        generator.write_rows(data)

        return generator.get_file_bytes()
