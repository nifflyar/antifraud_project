from dataclasses import dataclass

from app.application.common.interactor import Interactor
from app.domain.audit.repository import IAuditLogRepository
from app.domain.user.vo import UserId


@dataclass
class ListAuditLogsInputDTO:
    action: str | None = None
    user_id: UserId | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass
class AuditLogOutputDTO:
    id: str
    user_id: str | None
    action: str
    entity_type: str
    entity_id: str
    created_at: str
    meta: dict | None = None


@dataclass
class ListAuditLogsOutputDTO:
    logs: list[AuditLogOutputDTO]
    total: int
    limit: int
    offset: int


class ListAuditLogsInteractor(Interactor[ListAuditLogsInputDTO, ListAuditLogsOutputDTO]):
    def __init__(self, audit_repository: IAuditLogRepository) -> None:
        self.audit_repository = audit_repository

    async def __call__(self, data: ListAuditLogsInputDTO) -> ListAuditLogsOutputDTO:
        # Validate limit
        if data.limit > 1000:
            data.limit = 1000
        if data.limit < 1:
            data.limit = 1

        logs = []
        total = 0

        # Use appropriate repository method based on filters
        if data.action:
            logs = await self.audit_repository.get_all_by_action(data.action, data.limit)
            total = len(logs)
        elif data.user_id:
            logs = await self.audit_repository.get_all_by_user(data.user_id, data.limit)
            total = len(logs)
        elif data.entity_type and data.entity_id:
            logs = await self.audit_repository.get_all_by_entity(data.entity_type, data.entity_id)
            total = len(logs)
        else:
            # Fetch all audit logs with pagination
            logs, total = await self.audit_repository.get_all(data.limit, data.offset)

        # Convert to output DTOs
        # Note: offset/slicing is only needed for non-paginated queries
        if data.action or data.user_id or (data.entity_type and data.entity_id):
            output_logs = [
                AuditLogOutputDTO(
                    id=log.id,
                    user_id=str(log.user_id.value) if log.user_id else None,
                    action=log.action,
                    entity_type=log.entity_type,
                    entity_id=log.entity_id,
                    created_at=log.created_at.isoformat(),
                    meta=log.meta,
                )
                for log in logs[data.offset : data.offset + data.limit]
            ]
        else:
            # For get_all, pagination is handled by the repository
            output_logs = [
                AuditLogOutputDTO(
                    id=log.id,
                    user_id=str(log.user_id.value) if log.user_id else None,
                    action=log.action,
                    entity_type=log.entity_type,
                    entity_id=log.entity_id,
                    created_at=log.created_at.isoformat(),
                    meta=log.meta,
                )
                for log in logs
            ]

        return ListAuditLogsOutputDTO(
            logs=output_logs,
            total=total,
            limit=data.limit,
            offset=data.offset,
        )
