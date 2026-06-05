from dataclasses import dataclass
from datetime import datetime, UTC

from app.domain.user.vo import UserId, Email, UserRole, PasswordHash

@dataclass
class User:
    id: UserId
    full_name: str
    email: Email
    role: UserRole
    password_hash: PasswordHash
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login_at: datetime | None = None


    def has_role(self, role: UserRole) -> bool:
        return self.role == role

    def can_run_scoring(self) -> bool:
        return self.role.can_run_scoring()

    def can_manage_users(self) -> bool:
        return self.role.can_manage_users()

    def deactivate(self) -> None:
        self.is_active = False

    def change_role(self, new_role: UserRole) -> None:
        self.role = new_role

    @classmethod
    def create(cls, user_id: str, full_name: str,
               email: str, role: UserRole, password_hash: PasswordHash) -> "User":
        return cls(
            id=UserId(user_id),
            full_name=full_name,
            email=Email(email),
            role=role,
            password_hash=password_hash,
            is_admin=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )