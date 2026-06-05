from dataclasses import dataclass

from app.application.common.interactor import Interactor
from app.domain.user.repository import IUserRepository


@dataclass
class ListUsersInputDTO:
    limit: int = 20
    offset: int = 0


@dataclass
class UserOutputDTO:
    id: str
    email: str
    full_name: str
    is_admin: bool
    role: str
    is_active: bool
    created_at: str
    last_login_at: str | None = None


@dataclass
class ListUsersOutputDTO:
    users: list[UserOutputDTO]
    total: int
    limit: int
    offset: int


class ListUsersInteractor(Interactor[ListUsersInputDTO, ListUsersOutputDTO]):
    def __init__(self, user_repository: IUserRepository) -> None:
        self.user_repository = user_repository

    async def __call__(self, data: ListUsersInputDTO) -> ListUsersOutputDTO:
        # Validate limits
        if data.limit > 100:
            data.limit = 100
        if data.limit < 1:
            data.limit = 1

        users = await self.user_repository.get_all(limit=data.limit, offset=data.offset)

        # Convert to output DTOs
        output_users = [
            UserOutputDTO(
                id=str(user.id.value),
                email=user.email.value,
                full_name=user.full_name,
                is_admin=user.is_admin,
                role=user.role.value,
                is_active=user.is_active,
                created_at=user.created_at.isoformat() if user.created_at else "",
                last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            )
            for user in users
        ]

        return ListUsersOutputDTO(
            users=output_users,
            total=len(users),
            limit=data.limit,
            offset=data.offset,
        )
