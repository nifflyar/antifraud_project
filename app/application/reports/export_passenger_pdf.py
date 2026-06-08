import os
try:
    from fpdf import FPDF
except ImportError:
    from fpdf2 import FPDF

from app.application.common.timezone import ASTANA_TZ_LABEL, astana_now, format_astana_datetime
from app.domain.passenger.repository import IPassengerRepository
from app.domain.transaction.repository import ITransactionRepository
from app.domain.passenger.vo import PassengerId

class ExportPassengerProfilePdfInteractor:
    def __init__(
        self, 
        passenger_repo: IPassengerRepository,
        transaction_repo: ITransactionRepository
    ):
        self._passenger_repo = passenger_repo
        self._transaction_repo = transaction_repo

    async def execute(self, passenger_id: str) -> bytes:
        pid = PassengerId(int(passenger_id))
        profile = await self._passenger_repo.get_by_id(pid)
        if not profile:
            raise ValueError(f"Passenger with ID {passenger_id} not found")
        
        transactions = await self._transaction_repo.get_by_passenger_id(pid, limit=20)

        # Initialize PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Load and set font for Unicode support (Kazakh/Russian)
        # Font path relative to the container /app directory
        font_path = "/app/app/infrastructure/reports/assets/DejaVuSans.ttf"
        if not os.path.exists(font_path):
            # Fallback for local dev sessions if absolute path differs
            font_path = "app/infrastructure/reports/assets/DejaVuSans.ttf"
            
        pdf.add_font("DejaVu", "", font_path)
        pdf.set_font("DejaVu", size=14)

        # Header
        pdf.set_font("DejaVu", style="", size=16)
        pdf.cell(0, 10, "АНТИФРОД: ДОСЬЕ ПАССАЖИРА", ln=True, align="C")
        pdf.ln(5)

        # Basic Info Section
        pdf.set_font("DejaVu", style="", size=12)
        pdf.cell(0, 10, "Основная информация", ln=True)
        pdf.set_font("DejaVu", size=10)
        
        pdf.cell(50, 8, "ID Пассажира:", border=0)
        pdf.cell(0, 8, str(profile.id.value), border=0, ln=True)
        
        pdf.cell(50, 8, "ФИО (нормализовано):", border=0)
        pdf.cell(0, 8, profile.fio_clean or "Н/Д", border=0, ln=True)
        
        pdf.cell(62, 8, "ИИН/документ/телефон:", border=0)
        pdf.cell(0, 8, "скрыто", border=0, ln=True)

        if profile.score:
            pdf.ln(5)
            pdf.set_font("DejaVu", style="", size=12)
            pdf.cell(0, 10, "Оценка Риска", ln=True)
            pdf.set_font("DejaVu", size=10)
            
            risk_band = profile.score.risk_band.value.upper()
            pdf.cell(50, 8, "Категория риска:", border=0)
            pdf.cell(0, 8, risk_band, border=0, ln=True)
            
            pdf.cell(50, 8, "Финальный балл:", border=0)
            pdf.cell(0, 8, f"{profile.score.final_score:.2f}", border=0, ln=True)
            
            pdf.cell(50, 8, "Причины:", border=0)
            reasons = ", ".join(profile.score.top_reasons)
            pdf.multi_cell(0, 8, reasons or "Нет явных причин")

        # Transaction Table
        pdf.ln(10)
        pdf.set_font("DejaVu", style="", size=12)
        pdf.cell(0, 10, "Последние транзакции", ln=True)
        
        pdf.set_font("DejaVu", style="", size=9)
        # Column widths
        w = [40, 20, 25, 30, 75]
        
        pdf.cell(w[0], 8, "Дата GMT+5", 1)
        pdf.cell(w[1], 8, "Тип", 1)
        pdf.cell(w[2], 8, "Поезд", 1)
        pdf.cell(w[3], 8, "Сумма", 1)
        pdf.cell(w[4], 8, "Маршрут", 1, ln=True)

        pdf.set_font("DejaVu", size=8)
        for tx in transactions:
            pdf.cell(w[0], 8, format_astana_datetime(tx.op_datetime), 1)
            pdf.cell(w[1], 8, tx.op_type.value, 1)
            pdf.cell(w[2], 8, tx.train_no or "-", 1)
            pdf.cell(w[3], 8, f"{tx.amount:,.2f}", 1)
            # Route might contain long Kazakh names, use multi_cell or clip
            pdf.cell(w[4], 8, tx.route or "-", 1, ln=True)

        # Footer
        pdf.ln(20)
        pdf.set_font("DejaVu", style="", size=8)
        generated_at = astana_now().strftime("%d.%m.%Y %H:%M:%S")
        pdf.cell(0, 10, f"Отчет сформирован: {generated_at} ({ASTANA_TZ_LABEL})", align="R")

        pdf_bytes = pdf.output()
        if isinstance(pdf_bytes, str):
            return pdf_bytes.encode('latin-1')
        return pdf_bytes
