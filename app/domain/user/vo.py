from enum import Enum
from dataclasses import dataclass
import re

from app.domain.common.vo.integer import PositiveInteger
from app.domain.common.vo.string import NonEmptyString

class UserRole(str, Enum):
    ANALYST = "analyst"
    SECURITY = "security"
    ADMIN = "admin"

    def can_run_scoring(self) -> bool:
        return self in (UserRole.ADMIN,)

    def can_manage_users(self) -> bool:
        return self == UserRole.ADMIN

    def can_view_investigations(self) -> bool:
        return self in (UserRole.SECURITY, UserRole.ADMIN)


class UserId(PositiveInteger):
    pass


class Email(NonEmptyString):
    min_length = 3
    max_length = 320
    _EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z]+(?:[._][a-zA-Z0-9]+)*@"
        r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*(?:\."
        r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)+$"
    )

    def __init__(self, value: str) -> None:
        self._validate_type(value)
        normalized_value = value.strip().lower()
        self._validate(normalized_value)
        self._value = normalized_value

    @classmethod
    def _validate(cls, value: str) -> None:
        super()._validate(value)

        if any(char.isspace() for char in value):
            raise ValueError("Email value must not contain whitespace")

        if value.count("@") != 1:
            raise ValueError("Email value must contain a single @ separator")

        local_part, domain_part = value.split("@", 1)
        if not local_part or not domain_part:
            raise ValueError("Email value must have non-empty local and domain parts")

        if cls._EMAIL_PATTERN.fullmatch(value) is None:
            raise ValueError("Email value must match the allowed email format")
        

class PasswordHash(NonEmptyString):
    min_length = 1
    max_length = 1024

    def __init__(self, value: str) -> None:
        self._validate_type(value)
        if value == "":
            self._validate(value)
            return
        if not value.strip():
            raise ValueError("PasswordHash value must not be blank")

        normalized_value = value.strip()
        self._validate(normalized_value)
        self._value = normalized_value

    @classmethod
    def _validate(cls, value: str) -> None:
        super()._validate(value)