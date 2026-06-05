import uuid
from datetime import UTC, datetime
from typing import Any

from app.domain.audit.entity import AuditLog
from app.domain.audit.repository import IAuditLogRepository
from app.domain.user.vo import UserId


class AuditService:
    """Service for audit logging critical actions"""

    def __init__(self, audit_repository: IAuditLogRepository):
        self.audit_repository = audit_repository

    async def log_action(
        self,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        user_id: UserId | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Log an action to the audit trail"""
        log = AuditLog.create(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id or "",
            meta=meta or {},
        )
        await self.audit_repository.create_audit_log(log)

    async def log_login(self, user_id: UserId) -> None:
        """Log user login"""
        await self.log_action(
            action="LOGIN",
            entity_type="user",
            entity_id=str(user_id.value),
            user_id=user_id,
        )

    async def log_logout(self, user_id: UserId) -> None:
        """Log user logout"""
        await self.log_action(
            action="LOGOUT",
            entity_type="user",
            entity_id=str(user_id.value),
            user_id=user_id,
        )

    async def log_user_created(self, created_user_id: UserId, creator_id: UserId | None) -> None:
        """Log user creation"""
        await self.log_action(
            action="USER_CREATED",
            entity_type="user",
            entity_id=str(created_user_id.value),
            user_id=creator_id,
        )

    async def log_user_updated(self, user_id: UserId, updater_id: UserId, changes: dict[str, Any]) -> None:
        """Log user update"""
        await self.log_action(
            action="USER_UPDATED",
            entity_type="user",
            entity_id=str(user_id.value),
            user_id=updater_id,
            meta={"changes": changes},
        )

    async def log_upload_started(self, upload_id: str, user_id: UserId) -> None:
        """Log file upload started"""
        await self.log_action(
            action="UPLOAD_STARTED",
            entity_type="upload",
            entity_id=upload_id,
            user_id=user_id,
        )

    async def log_upload_completed(self, upload_id: str, user_id: UserId) -> None:
        """Log file upload completed"""
        await self.log_action(
            action="UPLOAD_COMPLETED",
            entity_type="upload",
            entity_id=upload_id,
            user_id=user_id,
        )

    async def log_scoring_started(self, upload_id: str, user_id: UserId) -> None:
        """Log scoring started"""
        await self.log_action(
            action="SCORING_STARTED",
            entity_type="scoring",
            entity_id=upload_id,
            user_id=user_id,
        )

    async def log_scoring_completed(self, upload_id: str, user_id: UserId) -> None:
        """Log scoring completed"""
        await self.log_action(
            action="SCORING_COMPLETED",
            entity_type="scoring",
            entity_id=upload_id,
            user_id=user_id,
        )
