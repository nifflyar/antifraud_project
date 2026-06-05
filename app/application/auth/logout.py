from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.common.interactor import Interactor
from app.application.interfaces.auth import AuthService
from app.domain.auth import RefreshSessionRepository


@dataclass
class LogoutInputDTO:
    refresh_token: str | None


class LogoutInteractor(Interactor[LogoutInputDTO, None]):
    def __init__(
        self,
        refresh_session_repository: RefreshSessionRepository,
        auth_service: AuthService,
    ) -> None:
        self.refresh_session_repository = refresh_session_repository
        self.auth_service = auth_service

    async def __call__(self, data: LogoutInputDTO) -> None:
        if data.refresh_token is None:
            return

        token_hash = self.auth_service.hash_refresh_token(data.refresh_token)
        refresh_session = await self.refresh_session_repository.get_session_by_token_hash(
            token_hash
        )
        if refresh_session is None or refresh_session.revoked_at is not None:
            return

        await self.refresh_session_repository.revoke_session(
            token_hash=token_hash,
            revoked_at=datetime.now(UTC),
        )
