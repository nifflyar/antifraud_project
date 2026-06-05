from dataclasses import dataclass

from app.application.common.interactor import Interactor
from app.domain.audit.repository import IAuditLogRepository


@dataclass
class GetAuditLogInputDTO:
    log_id: str


@dataclass
class GetAuditLogOutputDTO:
    id: str
    user_id: str | None
    action: str
    entity_type: str
    entity_id: str
    created_at: str
    meta: dict | None = None


class GetAuditLogInteractor(Interactor[GetAuditLogInputDTO, GetAuditLogOutputDTO]):
    def __init__(self, audit_repository: IAuditLogRepository) -> None:
        self.audit_repository = audit_repository

    async def __call__(self, data: GetAuditLogInputDTO) -> GetAuditLogOutputDTO:
        log = await self.audit_repository.get_by_id(data.log_id)

        if not log:
            raise ValueError(f"Audit log {data.log_id} not found")

        return GetAuditLogOutputDTO(
            id=log.id,
            user_id=str(log.user_id.value) if log.user_id else None,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            created_at=log.created_at.isoformat(),
            meta=log.meta,
        )
