from sqlalchemy import BIGINT, String

from app.domain.user.vo import (
    Email,
    PasswordHash,
    UserId,
)

from .base import VOType


class UserIdType(VOType):
    impl = BIGINT
    vo_class = UserId
    vo_raw = int
    cache_ok = True


class EmailType(VOType):
    impl = String(320)
    vo_class = Email
    vo_raw = str
    cache_ok = True


class PasswordHashType(VOType):
    impl = String(1024)
    vo_class = PasswordHash
    vo_raw = str
    cache_ok = True



