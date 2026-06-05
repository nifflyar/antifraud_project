from fastapi import APIRouter, Query, Depends, Request, HTTPException
from dishka.integrations.fastapi import FromDishka, inject
from datetime import datetime
from typing import Optional

from app.application.operations.list_suspicious import (
    ListOperationsInput,
    ListOperationsInteractor,
    ListSuspiciousOperationsInput,
    ListSuspiciousOperationsInteractor,
)
from app.presentation.api.operations.schemas import (
    OperationRiskStatsSchema,
    SuspiciousOperationsResponse,
    SuspiciousOperationSchema,
)

operations_router = APIRouter(prefix="/operations", tags=["Operations"])


def _operation_schema(tx, risk_band, operation_score, operation_reasons) -> SuspiciousOperationSchema:
    return SuspiciousOperationSchema(
        id=str(tx.id.value),
        passenger_id=str(tx.passenger_id.value) if tx.passenger_id else "",
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
        risk_band=risk_band,
        operation_risk_score=operation_score,
        operation_reasons=operation_reasons,
    )


@operations_router.get("", response_model=SuspiciousOperationsResponse)
@inject
async def list_operations(
    request: Request,
    interactor: FromDishka[ListOperationsInteractor],
    train_no: Optional[str] = Query(None),
    cashdesk: Optional[str] = Query(None),
    terminal: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    aggregator: Optional[str] = Query(None),
    point_of_sale: Optional[str] = Query(None),
    op_type: Optional[str] = Query(None, pattern="^(sale|refund|redeem|other)$"),
    search: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query("date", pattern="^(risk_score|risk_band|final_score|date|amount|train_no|passenger)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    include_risk_stats: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    claims = getattr(request.state, "auth_claims", None)
    if not claims:
        raise HTTPException(status_code=401, detail="Not authenticated")

    results, total, risk_stats = await interactor.execute(
        ListOperationsInput(
            train_no=train_no,
            cashdesk=cashdesk,
            terminal=terminal,
            channel=channel,
            aggregator=aggregator,
            point_of_sale=point_of_sale,
            op_type=op_type,
            search=search,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
            include_risk_stats=include_risk_stats,
        )
    )

    return SuspiciousOperationsResponse(
        items=[_operation_schema(tx, risk_band, operation_score, operation_reasons) for tx, risk_band, operation_score, operation_reasons in results],
        total=total,
        limit=limit,
        offset=offset,
        risk_stats=OperationRiskStatsSchema(**risk_stats) if risk_stats is not None else None,
    )


@operations_router.get("/suspicious", response_model=SuspiciousOperationsResponse)
@inject
async def get_suspicious_operations(
    request: Request,
    interactor: FromDishka[ListSuspiciousOperationsInteractor],
    train_no: Optional[str] = Query(None),
    cashdesk: Optional[str] = Query(None),
    terminal: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    aggregator: Optional[str] = Query(None),
    point_of_sale: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query("risk_score", pattern="^(risk_score|risk_band|final_score|date|amount|train_no|passenger)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    claims = getattr(request.state, "auth_claims", None)
    if not claims:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    input_dto = ListSuspiciousOperationsInput(
        train_no=train_no,
        cashdesk=cashdesk,
        terminal=terminal,
        channel=channel,
        aggregator=aggregator,
        point_of_sale=point_of_sale,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    results, total = await interactor.execute(input_dto)
    
    return SuspiciousOperationsResponse(
        items=[_operation_schema(tx, risk_band, operation_score, operation_reasons) for tx, risk_band, operation_score, operation_reasons in results],
        total=total,
        limit=limit,
        offset=offset
    )
