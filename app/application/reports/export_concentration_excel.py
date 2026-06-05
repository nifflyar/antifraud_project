from dataclasses import dataclass
from typing import List

from app.domain.risk.repository import IRiskConcentrationRepository
from app.domain.risk.vo import DimensionType
from app.application.common.reports import ExcelReportGenerator

class ExportRiskConcentrationExcelInteractor:
    def __init__(self, risk_repo: IRiskConcentrationRepository):
        self._risk_repo = risk_repo

    async def execute(self) -> bytes:
        dimensions = [
            (DimensionType.CHANNEL, "По каналам"),
            (DimensionType.AGGREGATOR, "По агрегаторам"),
            (DimensionType.TERMINAL, "По терминалам"),
            (DimensionType.CASHDESK, "По кассам")
        ]

        generator = ExcelReportGenerator(title="Концентрация рисков")
        
        # We'll put all dimensions into one long sheet or separate them
        # For simplicity, let's put them sequentially with headers
        
        for dim_type, label in dimensions:
            concentrations = await self._risk_repo.get_all_by_dimension(dim_type)
            
            # Write a section header
            current_row = generator.ws.max_row + (2 if generator.ws.max_row > 1 else 0)
            cell = generator.ws.cell(row=current_row, column=1, value=f"АНАЛИЗ: {label.upper()}")
            cell.font = generator.header_font
            cell.fill = generator.header_fill
            
            headers = ["Значение измерения", "Всего операций", "Подозрительных", "Доля риска (%)", "Лифт"]
            for col_num, h in enumerate(headers, 1):
                c = generator.ws.cell(row=current_row + 1, column=col_num, value=h)
                c.font = generator.header_font
                c.fill = generator.header_fill

            data = []
            for c in concentrations:
                data.append([
                    c.dimension_value,
                    c.total_ops,
                    c.highrisk_ops,
                    round(c.share_highrisk_ops, 2),
                    round(c.lift_vs_base, 2)
                ])
            
            # Manual write since write_rows assumes start at row 2
            for r_idx, r_data in enumerate(data, current_row + 2):
                for c_idx, val in enumerate(r_data, 1):
                    generator.ws.cell(row=r_idx, column=c_idx, value=val)

        return generator.get_file_bytes()
