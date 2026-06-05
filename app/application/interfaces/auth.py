from abc import abstractmethod
from typing import Protocol


class AuthService(Protocol):
    @abstractmethod
    def hash_password(self, password: str) -> str: ...

    @abstractmethod
    def verify_password(self, password: str, password_hash: str) -> bool: ...

    @abstractmethod
    def create_access_token(self, user_id: int, is_admin: bool) -> str: ...

    @abstractmethod
    def create_refresh_token(self) -> str: ...

    @abstractmethod
    def hash_refresh_token(self, refresh_token: str) -> str: ...
