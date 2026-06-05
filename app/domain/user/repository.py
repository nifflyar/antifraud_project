from abc import ABC, abstractmethod
from app.domain.user.entity import User
from app.domain.user.vo import UserId, Email

class IUserRepository(ABC):

    @abstractmethod
    async def get_by_id(self, user_id: UserId) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None: ...

    @abstractmethod
    async def create_user(self, user: User) -> User: ...

    @abstractmethod
    async def get_all(self, limit: int = 20, offset: int = 0) -> list[User]: ...

    @abstractmethod
    async def update_user(self, user: User) -> User: ...

    @abstractmethod
    async def delete_user(self, user_id: UserId) -> None: ...

    @abstractmethod
    async def any_users_exist(self) -> bool: ...

    @abstractmethod
    async def count_admins(self) -> int: ...