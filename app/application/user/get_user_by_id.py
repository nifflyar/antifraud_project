from dataclasses import dataclass

from app.application.common.interactor import Interactor
from app.domain.user.repository import IUserRepository
from app.domain.user.vo import UserId


@dataclass
class GetUserByIdInputDTO:
    user_id: UserId


@dataclass
class GetUserByIdOutputDTO:
    id: str
    email: str
    full_name: str
    is_admin: bool
    role: str
    is_active: bool
    created_at: str
    last_login_at: str | None = None


class GetUserByIdInteractor(Interactor[GetUserByIdInputDTO, GetUserByIdOutputDTO]):
    def __init__(self, user_repository: IUserRepository) -> None:
        self.user_repository = user_repository

    async def __call__(self, data: GetUserByIdInputDTO) -> GetUserByIdOutputDTO:
        user = await self.user_repository.get_by_id(data.user_id)

        if not user:
            raise ValueError(f"User {data.user_id.value} not found")

        return GetUserByIdOutputDTO(
            id=str(user.id.value),
            email=user.email.value,
            full_name=user.full_name,
            is_admin=user.is_admin,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        )
