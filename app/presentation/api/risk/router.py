from fastapi import APIRouter, Query, Depends, Request, HTTPException
from dishka.integrations.fastapi import FromDishka, inject
from typing import Optional

from app.application.dashboard.get_risk_concentration import GetRiskConcentrationInteractor

risk_router = APIRouter(prefix="/risk", tags=["Risk Concentration"])

@risk_router.get("/{dimension_type}")
@inject
async def get_risk_concentration(
    request: Request,
    dimension_type: str,
    interactor: FromDishka[GetRiskConcentrationInteractor]
):
    claims = getattr(request.state, "auth_claims", None)
    if not claims:
        raise HTTPException(status_code=401, detail="Not authenticated")
    """
    Returns risk concentration statistics for a given dimension.
    Supported types: channel, aggregator, terminal, cashdesk.
    """
    return await interactor.execute(dimension_type)
