from fastapi import APIRouter, Query, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from dishka.integrations.fastapi import FromDishka, inject
from datetime import datetime
from typing import Optional
import io

from app.application.reports.export_suspicious_excel import ExportSuspiciousOperationsExcelInteractor, ExportSuspiciousInput
from app.application.reports.export_concentration_excel import ExportRiskConcentrationExcelInteractor
from app.application.reports.export_passenger_pdf import ExportPassengerProfilePdfInteractor
from app.application.reports.export_passengers_excel import ExportPassengersByRiskExcelInteractor, ExportPassengersByRiskInput
from app.domain.passenger.vo import RiskBand

reports_router = APIRouter(prefix="/reports", tags=["Reports"])

@reports_router.get("/operations/suspicious/excel")
@inject
async def download_suspicious_excel(
    request: Request,
    interactor: FromDishka[ExportSuspiciousOperationsExcelInteractor],
    train_no: Optional[str] = Query(None),
    cashdesk: Optional[str] = Query(None),
    terminal: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    claims = getattr(request.state, "auth_claims", None)
    if not claims:
        raise HTTPException(status_code=401, detail="Not authenticated")

    input_dto = ExportSuspiciousInput(
        train_no=train_no,
        cashdesk=cashdesk,
        terminal=terminal,
        date_from=date_from,
        date_to=date_to
    )
    
    file_bytes = await interactor.execute(input_dto)
    
    filename = f"suspicious_ops_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@reports_router.get("/risk-concentration/excel")
@inject
async def download_concentration_excel(
    request: Request,
    interactor: FromDishka[ExportRiskConcentrationExcelInteractor],
):
    claims = getattr(request.state, "auth_claims", None)
    if not claims:
        raise HTTPException(status_code=401, detail="Not authenticated")

    file_bytes = await interactor.execute()
    
    filename = f"risk_concentration_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@reports_router.get("/passengers/{passenger_id}/pdf")
@inject
async def download_passenger_pdf(
    request: Request,
    passenger_id: str,
    interactor: FromDishka[ExportPassengerProfilePdfInteractor],
):
    claims = getattr(request.state, "auth_claims", None)
    if not claims:
        raise HTTPException(status_code=401, detail="Not authenticated")

    file_bytes = await interactor.execute(passenger_id)

    filename = f"passenger_{passenger_id}_dossier.pdf"
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@reports_router.get("/passengers/excel")
@inject
async def download_passengers_excel(
    request: Request,
    interactor: FromDishka[ExportPassengersByRiskExcelInteractor],
    risk_band: Optional[RiskBand] = Query(None, description="Фильтр по риск-зоне: low, medium, high, critical"),
    search: Optional[str] = Query(None, description="Поиск по ФИО или ИИН"),
):
    claims = getattr(request.state, "auth_claims", None)
    if not claims:
        raise HTTPException(status_code=401, detail="Not authenticated")

    input_dto = ExportPassengersByRiskInput(
        risk_band=risk_band,
        search=search
    )

    file_bytes = await interactor.execute(input_dto)

    risk_label = risk_band.value if risk_band else "all"
    filename = f"passengers_{risk_label}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
