from fastapi import APIRouter, HTTPException, Query, Depends, Request
from dishka.integrations.fastapi import FromDishka, inject
from typing import Optional
from dataclasses import asdict

from app.domain.passenger.vo import RiskBand
from app.domain.passenger.repository import IPassengerRepository
from app.application.passenger.list_passengers import ListPassengersInteractor
from app.application.passenger.get_passenger_profile import GetPassengerProfileInteractor
from app.application.passenger.get_passenger_transactions import GetPassengerTransactionsInteractor
from app.application.passenger.override_risk import OverridePassengerRiskInteractor, OverrideRiskInput
from app.application.passenger.get_risk_stats import GetPassengerRiskStatsInteractor
from app.presentation.api.passenger.schemas import (
    PassengerListResponse,
    PassengerProfileResponse,
    PassengerTransactionSchema,
    PassengerTransactionsResponse,
    PassengerListItemSchema,
    RiskOverrideRequest
)

passenger_router = APIRouter(prefix="/passengers", tags=["Passengers"])

@passenger_router.get("", response_model=PassengerListResponse)
@inject
async def list_passengers(
    interactor: FromDishka[ListPassengersInteractor],
    risk_band: Optional[RiskBand] = Query(None),
    search: Optional[str] = Query(None, description="Поиск по ФИО или ИИН"),
    sort_by: str = Query("risk_band", description="Поле для сортировки"),
    sort_order: str = Query("desc", description="Порядок сортировки: asc или desc"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Получение списка пассажиров с фильтрацией по риску и поиском.
    """
    result = await interactor.execute(
        risk_band=risk_band,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

    items = [
        PassengerListItemSchema(
            id=str(p.id.value),
            fio_clean=p.fio_clean,
            fake_fio_score=p.fake_fio_score,
            last_seen_at=p.last_seen_at,
            risk_band=p.score.risk_band if p.score else RiskBand.low,
            final_score=p.score.final_score if p.score else 0.0
        )
        for p in result.items
    ]

    return PassengerListResponse(
        items=items,
        total=result.total,
        limit=result.limit,
        offset=result.offset
    )

@passenger_router.get("/v2/list", response_model=dict)
@inject
async def list_passengers_cursor(
    repo: FromDishka[IPassengerRepository],
    risk_band: Optional[RiskBand] = Query(None),
    search: Optional[str] = Query(None, description="Поиск по ФИО или ИИН"),
    sort_by: str = Query("risk_band", description="Поле для сортировки"),
    sort_order: str = Query("desc", description="Порядок сортировки: asc или desc"),
    cursor: Optional[str] = Query(None, description="Cursor from previous response"),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Cursor-based pagination for passengers (O(1) instead of O(n)).
    Use 'cursor' from next_cursor in previous response for next page.
    """
    page = await repo.get_all_cursor(
        risk_band=risk_band,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        cursor=cursor,
        limit=limit,
    )

    return {
        "items": [
            {
                "id": str(p.id.value),
                "fio_clean": p.fio_clean,
                "fake_fio_score": p.fake_fio_score,
                "last_seen_at": p.last_seen_at,
                "risk_band": p.score.risk_band if p.score else RiskBand.low,
                "final_score": p.score.final_score if p.score else 0.0,
            }
            for p in page.items
        ],
        "next_cursor": page.next_cursor,
        "prev_cursor": page.prev_cursor,
        "has_more": page.has_more,
    }

@passenger_router.get("/{passenger_id}", response_model=PassengerProfileResponse)
@inject
async def get_passenger(
    passenger_id: int,
    interactor: FromDishka[GetPassengerProfileInteractor],
):
    """
    Получение детального профиля пассажира (баллы, признаки).
    """
    passenger = await interactor.execute(passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passenger not found")

    fake_fio_score = passenger.fake_fio_score
    if passenger.features:
        # ETL stores passenger.fake_fio_score on a 0..1 scale; ML feature
        # fio_fake_score_max is 0..10. Expose the strongest available signal on
        # the profile header as 0..1 so old uploads benefit from improved ML
        # identity scoring without requiring a full re-import.
        fake_fio_score = max(fake_fio_score, min(passenger.features.fio_fake_score_max / 10, 1.0))
    
    return PassengerProfileResponse(
        id=str(passenger.id.value),
        fio_clean=passenger.fio_clean,
        fake_fio_score=fake_fio_score,
        first_seen_at=passenger.first_seen_at,
        last_seen_at=passenger.last_seen_at,
        identity=asdict(passenger.identity) if passenger.identity else None,
        features=asdict(passenger.features) if passenger.features else None,
        score=asdict(passenger.score) if passenger.score else None
    )

@passenger_router.get("/{passenger_id}/transactions", response_model=PassengerTransactionsResponse)
@inject
async def get_passenger_transactions(
    passenger_id: int,
    interactor: FromDishka[GetPassengerTransactionsInteractor],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    История транзакций конкретного пассажира.
    """
    result = await interactor.execute(passenger_id, limit, offset)
    
    return PassengerTransactionsResponse(
        items=[
            PassengerTransactionSchema(
                id=str(tx.id.value),
                op_type=tx.op_type.value,
                op_datetime=tx.op_datetime,
                dep_datetime=tx.dep_datetime,
                train_no=tx.train_no,
                amount=tx.amount,
                fee=tx.fee,
                channel=tx.channel,
                aggregator=tx.aggregator,
                terminal=tx.terminal,
                cashdesk=tx.cashdesk,
                point_of_sale=tx.point_of_sale,
                order_no=tx.order_no,
                ticket_no=tx.ticket_no,
                tariff_type=tx.tariff_type,
                service_class=tx.service_class,
                dep_station=tx.dep_station,
                arr_station=tx.arr_station,
                route=tx.route,
                fio=tx.fio,
                iin=tx.iin,
                doc_no=tx.doc_no,
                phone=tx.phone,
                gender=tx.gender,
                branch=tx.branch,
                sale_user=tx.sale_user,
                carrier=tx.carrier,
                settlement_type=tx.settlement_type,
            )
            for tx in result.items
        ],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )

@passenger_router.post("/{passenger_id}/override")
@inject
async def override_risk(
    request: Request,
    passenger_id: int,
    data: RiskOverrideRequest,
    interactor: FromDishka[OverridePassengerRiskInteractor],
):
    claims = getattr(request.state, "auth_claims", None)
    if not claims or not claims.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can override risk levels")

    input_dto = OverrideRiskInput(
        passenger_id=passenger_id,
        new_risk_band=data.new_risk_band,
        reason=data.reason,
        actor_user_id=claims.user_id
    )
    await interactor.execute(input_dto)
    return {"status": "success", "message": "Risk level overridden successfully"}

@passenger_router.get("/stats/risk-bands")
@inject
async def get_risk_stats(
    interactor: FromDishka[GetPassengerRiskStatsInteractor],
    search: Optional[str] = Query(None, description="Поиск по ФИО или ИИН"),
):
    """
    Получение статистики пассажиров по группам риска.
    """
    stats = await interactor.execute(search=search)
    return {
        "critical": stats.critical,
        "high": stats.high,
        "medium": stats.medium,
        "low": stats.low,
        "unscored": stats.unscored,
        "total": stats.total,
    }
