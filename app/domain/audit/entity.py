from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any

from app.domain.user.vo import UserId

@dataclass(frozen=True)   # Immutable: create and forget
class AuditLog:
    id: str
    user_id: UserId
    action: str
    entity_type: str
    entity_id: str
    created_at: datetime
    meta: dict[str, Any] | None

    @classmethod
    def create(
        cls,
        log_id: str,
        user_id: UserId,
        action: str,
        entity_type: str,
        entity_id: str,
        meta: dict | None = None,
    ) -> "AuditLog":
        return cls(
            id=log_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            created_at=datetime.now(UTC),
            meta=meta or {},
        )