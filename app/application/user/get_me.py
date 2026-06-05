from dataclasses import dataclass

from app.application.common.interactor import Interactor
from app.application.user.exceptions import UserNotFoundError
from app.domain.user.repository import IUserRepository
from app.domain.user.vo import UserId


@dataclass
class GetUserProfileInputDTO:
    user_id: UserId


@dataclass
class GetUserProfileOutputDTO:
    id: str
    email: str
    full_name: str
    is_admin: bool
    created_at: str


class GetUserProfileInteractor(
    Interactor[GetUserProfileInputDTO, GetUserProfileOutputDTO]
):
    def __init__(self, user_repository: IUserRepository) -> None:
        self.user_repository = user_repository

    async def __call__(self, data: GetUserProfileInputDTO) -> GetUserProfileOutputDTO:
        user = await self.user_repository.get_by_id(data.user_id)

        if not user:
            raise UserNotFoundError(data.user_id)


        return GetUserProfileOutputDTO(
            id=str(user.id.value),
            email=user.email.value,
            full_name=user.full_name,
            is_admin=user.is_admin,
            created_at=user.created_at.isoformat() if user.created_at else "",
        )
