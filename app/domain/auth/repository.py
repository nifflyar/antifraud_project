from abc import abstractmethod
from datetime import datetime
from typing import Protocol

from .entity import RefreshSession


class RefreshSessionRepository(Protocol):
    @abstractmethod
    async def get_session_by_token_hash(self, token_hash: str) -> RefreshSession | None: ...

    @abstractmethod
    async def create_session(self, session: RefreshSession) -> RefreshSession: ...

    @abstractmethod
    async def revoke_session(
        self, token_hash: str, revoked_at: datetime
    ) -> RefreshSession | None: ...
