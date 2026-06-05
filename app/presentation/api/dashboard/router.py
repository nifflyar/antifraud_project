from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from dishka.integrations.fastapi import FromDishka, inject
from typing import Optional
import asyncio

from app.application.dashboard.get_summary import GetDashboardSummaryInteractor
from app.application.dashboard.get_risk_trend import GetRiskTrendInteractor
from app.application.dashboard.get_risk_concentration import GetRiskConcentrationInteractor
from app.application.dashboard.get_risk_stats import GetRiskStatsInteractor
from app.application.passenger.list_passengers import ListPassengersInteractor
from app.domain.passenger.vo import RiskBand
from app.presentation.api.dashboard.schemas import (
    DashboardSummaryResponse,
    RiskTrendResponse,
    RiskConcentrationResponse,
    RiskStatsResponse
)

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@dashboard_router.get("/summary", response_model=DashboardSummaryResponse)
@inject
async def get_summary(
    interactor: FromDishka[GetDashboardSummaryInteractor],
):
    """
    Получение общих метрик по системе (кол-во пассажиров, риски, топ каналы).
    """
    return await interactor.execute()

@dashboard_router.get("/risk-trend", response_model=RiskTrendResponse)
@inject
async def get_risk_trend(
    interactor: FromDishka[GetRiskTrendInteractor],
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    """
    Получение тренда рисков по дням.
    """
    return await interactor.execute(date_from=date_from, date_to=date_to)

@dashboard_router.get("/risk-concentration", response_model=RiskConcentrationResponse)
@inject
async def get_risk_concentration(
    interactor: FromDishka[GetRiskConcentrationInteractor],
    dimension_type: str = Query(..., description="Разрез: CHANNEL, AGGREGATOR, TERMINAL, CASHDESK"),
    live: bool = Query(False, description="Точный live-расчет для детальных вкладок"),
):
    """
    Получение концентрации рисков по выбранному разрезу.
    """
    try:
        return await interactor.execute(dimension_type=dimension_type, live=live)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@dashboard_router.get("/risk-stats", response_model=RiskStatsResponse)
@inject
async def get_risk_stats(
    interactor: FromDishka[GetRiskStatsInteractor],
    period: str = Query("all", description="Period: all, today, week, month"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    """
    Получение статистики рисков за период с процентами по рискам.
    """
    return await interactor.execute(period=period, date_from=date_from, date_to=date_to)

@dashboard_router.get("/combined", response_model=dict)
@inject
async def get_dashboard_combined(
    summary_interactor: FromDishka[GetDashboardSummaryInteractor],
    stats_interactor: FromDishka[GetRiskStatsInteractor],
    passengers_interactor: FromDishka[ListPassengersInteractor],
    period: str = Query("all", description="Period: all, today, week, month"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    """
    Combined dashboard data: summary + risk-stats + top 5 critical passengers.
    Single atomic call instead of 3 separate requests.
    """
    summary, stats, passengers_result = await asyncio.gather(
        summary_interactor.execute(),
        stats_interactor.execute(period=period, date_from=date_from, date_to=date_to),
        passengers_interactor.execute(
            risk_band=RiskBand.critical,
            limit=5,
            offset=0,
        ),
    )

    return {
        "summary": summary.dict() if hasattr(summary, 'dict') else summary,
        "riskStats": stats.dict() if hasattr(stats, 'dict') else stats,
        "topCritical": [
            {
                "id": str(p.id.value),
                "fio_clean": p.fio_clean,
                "fake_fio_score": p.fake_fio_score,
                "last_seen_at": p.last_seen_at,
                "risk_band": p.score.risk_band if p.score else RiskBand.low,
                "final_score": p.score.final_score if p.score else 0.0,
            }
            for p in passengers_result.items
        ],
    }
