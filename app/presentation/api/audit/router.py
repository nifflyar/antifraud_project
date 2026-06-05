from fastapi import APIRouter, Query, HTTPException, status, Request
from dishka.integrations.fastapi import FromDishka, inject

from app.application.audit import (
    ListAuditLogsInteractor,
    ListAuditLogsInputDTO,
    ListAuditLogsOutputDTO,
    GetAuditLogInteractor,
    GetAuditLogInputDTO,
    GetAuditLogOutputDTO,
)
from app.domain.user.vo import UserId
from app.infrastructure.config import Config
from app.presentation.api.security import get_optional_auth_claims_from_request


router = APIRouter(prefix="/audit-logs", tags=["audit"])


def _check_admin_access(claims) -> None:
    """Check if user has admin access"""
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    if not claims.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access audit logs",
        )


@router.get("", response_model=ListAuditLogsOutputDTO)
@inject
async def list_audit_logs(
    request: Request,
    config: FromDishka[Config],
    action: str | None = Query(None),
    user_id: int | None = Query(None),
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    interactor: FromDishka[ListAuditLogsInteractor] = None,
) -> ListAuditLogsOutputDTO:
    """List audit logs with optional filters. Admin only."""
    claims = get_optional_auth_claims_from_request(request, config)
    _check_admin_access(claims)

    return await interactor(
        ListAuditLogsInputDTO(
            action=action,
            user_id=UserId(user_id) if user_id else None,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/{log_id}", response_model=GetAuditLogOutputDTO)
@inject
async def get_audit_log(
    request: Request,
    config: FromDishka[Config],
    log_id: str,
    interactor: FromDishka[GetAuditLogInteractor] = None,
) -> GetAuditLogOutputDTO:
    """Get specific audit log details. Admin only."""
    claims = get_optional_auth_claims_from_request(request, config)
    _check_admin_access(claims)

    try:
        return await interactor(GetAuditLogInputDTO(log_id=log_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )


audit_router = router
