from dataclasses import dataclass
from datetime import UTC, datetime
import secrets

from app.application.common.exceptions import ValidationError
from app.application.common.interactor import Interactor
from app.application.interfaces.auth import AuthService
from app.domain.user.entity import User
from app.domain.user.repository import IUserRepository
from app.domain.user.vo import (
    Email,
    PasswordHash,
    UserId,
    UserRole,
)


@dataclass
class RegisterInputDTO:
    email: str
    password: str
    full_name: str
    actor_user_id: UserId | None
    is_admin: bool = False


@dataclass
class RegisterOutputDTO:
    user_id: UserId
    email: str


class RegisterInteractor(Interactor[RegisterInputDTO, RegisterOutputDTO]):
    def __init__(
        self,
        user_repository: IUserRepository,
        auth_service: AuthService,
        admin_emails: set[str],
    ) -> None:
        self.user_repository = user_repository
        self.auth_service = auth_service
        self.admin_emails = {email.strip().lower() for email in admin_emails}

    async def __call__(self, data: RegisterInputDTO) -> RegisterOutputDTO:
        email = Email(data.email)
        full_name = data.full_name

        if len(data.password) < 8:
            raise ValidationError("Password must be at least 8 characters long")

        if data.actor_user_id is None:
            if await self.user_repository.any_users_exist():
                raise ValidationError("Only admins can register users")
            if email.value not in self.admin_emails:
                raise ValidationError("Only admins can register users")
            created_is_admin = True
        else:
            actor = await self.user_repository.get_by_id(data.actor_user_id)
            if actor is None or not actor.is_admin:
                raise ValidationError("Only admins can register users")
            created_is_admin = data.is_admin

        existing_user = await self.user_repository.get_by_email(email)
        if existing_user is not None:
            raise ValidationError("Email already registered")

        now = datetime.now(UTC)
        password_hash = PasswordHash(self.auth_service.hash_password(data.password))
        user = User(
            id=UserId(secrets.randbelow(2**63 - 1) + 1),
            email=email,
            password_hash=password_hash,
            full_name=data.full_name,
            role=UserRole.ANALYST,
            is_admin=created_is_admin,
            created_at=now,
            updated_at=now,
            last_login_at=now,
        )
        await self.user_repository.create_user(user)

        return RegisterOutputDTO(user_id=user.id, email=user.email.value)
