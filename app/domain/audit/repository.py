from abc import ABC, abstractmethod

from app.domain.user.vo import UserId
from app.domain.audit.entity import AuditLog

class IAuditLogRepository(ABC):

    @abstractmethod
    async def create_audit_log(self, log: AuditLog) -> None: ...

    @abstractmethod
    async def get_by_id(self, log_id: str) -> AuditLog | None: ...

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> tuple[list[AuditLog], int]: ...

    @abstractmethod
    async def get_all_by_user(
        self, user_id: UserId, limit: int = 100
    ) -> list[AuditLog]: ...

    @abstractmethod
    async def get_all_by_entity(
        self, entity_type: str, entity_id: str
    ) -> list[AuditLog]: ...

    @abstractmethod
    async def get_all_by_action(
        self, action: str, limit: int = 100
    ) -> list[AuditLog]: ...

    @abstractmethod
    async def get_all_by_date_range(
        self, date_from: str, date_to: str, limit: int = 100
    ) -> list[AuditLog]: ...