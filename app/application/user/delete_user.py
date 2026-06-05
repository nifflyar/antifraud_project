from dataclasses import dataclass

from app.application.common.interactor import Interactor
from app.application.common.exceptions import ValidationError
from app.application.services.audit import AuditService
from app.domain.user.repository import IUserRepository
from app.domain.user.vo import UserId


@dataclass
class DeleteUserInputDTO:
    user_id: UserId
    actor_user_id: UserId  # Admin performing deletion


class DeleteUserInteractor(Interactor[DeleteUserInputDTO, None]):
    def __init__(
        self,
        user_repository: IUserRepository,
        audit_service: AuditService,
    ) -> None:
        self.user_repository = user_repository
        self.audit_service = audit_service

    async def __call__(self, data: DeleteUserInputDTO) -> None:
        # Verify actor is admin
        actor = await self.user_repository.get_by_id(data.actor_user_id)
        if not actor or not actor.is_admin:
            raise ValidationError("Only admins can delete users")

        user = await self.user_repository.get_by_id(data.user_id)
        if not user:
            raise ValueError(f"User {data.user_id.value} not found")

        # Prevent deletion of the last admin
        if user.is_admin:
            # Count remaining admins using efficient SQL query
            admin_count = await self.user_repository.count_admins()
            if admin_count <= 1:
                raise ValidationError("Cannot delete the last admin user")

        # Delete user
        await self.user_repository.delete_user(data.user_id)

        # Log deletion
        await self.audit_service.log_action(
            action="USER_DELETED",
            entity_type="user",
            entity_id=str(user.id.value),
            user_id=data.actor_user_id,
            meta={"email": user.email.value, "is_admin": user.is_admin},
        )
