from datetime import datetime

from sqlalchemy import BOOLEAN, TIMESTAMP, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.user.vo import (
    Email,
    PasswordHash,
    UserId,
    UserRole,
)

from .base import BaseORMModel
from .types.user import (
    EmailType,
    PasswordHashType,
    UserIdType,
)


class UserModel(BaseORMModel):
    __tablename__ = "users"

    id: Mapped[UserId] = mapped_column(UserIdType, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[Email] = mapped_column(EmailType, unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole", create_type=False, native_enum=False),
        nullable=False,
        default=UserRole.ANALYST,
    )
    password_hash: Mapped[PasswordHash] = mapped_column(PasswordHashType, nullable=False)
    is_active: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, server_default="true")
    is_admin: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
