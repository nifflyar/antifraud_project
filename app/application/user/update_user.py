from dataclasses import dataclass

from app.application.common.interactor import Interactor
from app.application.common.exceptions import ValidationError
from app.application.services.audit import AuditService
from app.domain.user.repository import IUserRepository
from app.domain.user.vo import UserId


@dataclass
class UpdateUserInputDTO:
    user_id: UserId
    actor_user_id: UserId | None  # User making the change
    full_name: str | None = None
    is_admin: bool | None = None


@dataclass
class UpdateUserOutputDTO:
    id: str
    email: str
    full_name: str
    is_admin: bool


class UpdateUserInteractor(Interactor[UpdateUserInputDTO, UpdateUserOutputDTO]):
    def __init__(
        self,
        user_repository: IUserRepository,
        audit_service: AuditService,
    ) -> None:
        self.user_repository = user_repository
        self.audit_service = audit_service

    async def __call__(self, data: UpdateUserInputDTO) -> UpdateUserOutputDTO:
        # Only admin can update
        if data.actor_user_id:
            actor = await self.user_repository.get_by_id(data.actor_user_id)
            if not actor or not actor.is_admin:
                raise ValidationError("Only admins can update users")
        else:
            # No actor means self-update of limited fields
            data.actor_user_id = data.user_id

        user = await self.user_repository.get_by_id(data.user_id)
        if not user:
            raise ValueError(f"User {data.user_id.value} not found")

        # Track changes for audit log
        changes = {}

        if data.full_name is not None and data.full_name != user.full_name:
            changes["full_name"] = {"old": user.full_name, "new": data.full_name}
            user.full_name = data.full_name

        if data.is_admin is not None and data.is_admin != user.is_admin:
            changes["is_admin"] = {"old": user.is_admin, "new": data.is_admin}
            user.is_admin = data.is_admin

        if changes:
            await self.user_repository.update_user(user)

            # Log changes
            await self.audit_service.log_action(
                action="USER_UPDATED",
                entity_type="user",
                entity_id=str(user.id.value),
                user_id=data.actor_user_id,
                meta={"changes": changes},
            )

        return UpdateUserOutputDTO(
            id=str(user.id.value),
            email=user.email.value,
            full_name=user.full_name,
            is_admin=user.is_admin,
        )
