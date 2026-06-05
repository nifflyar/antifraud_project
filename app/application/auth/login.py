from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from app.application.auth.exceptions import InvalidAuthDataError
from app.application.common.interactor import Interactor
from app.application.common.transaction import TransactionManager
from app.application.interfaces.auth import AuthService
from app.domain.auth import RefreshSession, RefreshSessionRepository
from app.domain.user.repository import IUserRepository
from app.domain.user.vo import Email


@dataclass
class LoginInputDTO:
    email: str
    password: str


@dataclass
class LoginOutputDTO:
    user_id: int
    is_admin: bool
    refresh_token: str


class LoginInteractor(Interactor[LoginInputDTO, LoginOutputDTO]):
    def __init__(
        self,
        user_repository: IUserRepository,
        refresh_session_repository: RefreshSessionRepository,
        auth_service: AuthService,
        transaction_manager: TransactionManager,
        admin_emails: set[str],
        refresh_token_expire_days: int,
    ) -> None:
        self.user_repository = user_repository
        self.refresh_session_repository = refresh_session_repository
        self.auth_service = auth_service
        self.transaction_manager = transaction_manager
        self.admin_emails = {email.strip().lower() for email in admin_emails}
        self.refresh_token_expire_days = refresh_token_expire_days

    async def __call__(self, data: LoginInputDTO) -> LoginOutputDTO:
        user = await self.user_repository.get_by_email(Email(data.email))
        if user is None:
            raise InvalidAuthDataError("Invalid credentials")

        if not self.auth_service.verify_password(data.password, user.password_hash.value):
            raise InvalidAuthDataError("Invalid credentials")

        now = datetime.now(UTC)
        should_be_admin = user.email.value in self.admin_emails
        updated_user = replace(
            user,
            is_admin=should_be_admin,
            updated_at=now,
            last_login_at=now,
        )
        updated_user = await self.user_repository.update_user(updated_user)

        refresh_token = self.auth_service.create_refresh_token()
        refresh_session = RefreshSession(
            token_hash=self.auth_service.hash_refresh_token(refresh_token),
            user_id=updated_user.id,
            expires_at=now + timedelta(days=self.refresh_token_expire_days),
            created_at=now,
            revoked_at=None,
        )
        await self.refresh_session_repository.create_session(refresh_session)
        return LoginOutputDTO(
            user_id=updated_user.id.value,
            is_admin=updated_user.is_admin,
            refresh_token=refresh_token,
        )
