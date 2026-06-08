from dataclasses import dataclass

from app.application.common.interactor import Interactor
from app.application.common.exceptions import ValidationError
from app.application.services.audit import AuditService
from app.domain.user.repository import IUserRepository
from app.domain.user.vo import UserId, UserRole


@dataclass
class UpdateUserInputDTO:
    user_id: UserId
    actor_user_id: UserId | None  # User making the change
    full_name: str | None = None
    is_admin: bool | None = None
    role: str | None = None
    is_active: bool | None = None


@dataclass
class UpdateUserOutputDTO:
    id: str
    email: str
    full_name: str
    is_admin: bool
    role: str
    is_active: bool
    created_at: str
    last_login_at: str | None = None


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

        is_self_update = data.actor_user_id.value == data.user_id.value

        requested_role: UserRole | None = None
        if data.role is not None:
            try:
                requested_role = UserRole(data.role)
            except ValueError as exc:
                raise ValidationError("Invalid user role") from exc

        # Track changes for audit log
        changes = {}

        if data.full_name is not None:
            full_name = data.full_name.strip()
            if not full_name:
                raise ValidationError("Full name is required")
            if full_name != user.full_name:
                changes["full_name"] = {"old": user.full_name, "new": full_name}
                user.full_name = full_name

        next_role = requested_role if requested_role is not None else user.role
        next_is_admin = data.is_admin if data.is_admin is not None else user.is_admin
        if requested_role is not None:
            next_is_admin = requested_role == UserRole.ADMIN
        elif data.is_admin is not None:
            next_role = UserRole.ADMIN if data.is_admin else (UserRole.ANALYST if user.role == UserRole.ADMIN else user.role)

        demotes_admin = user.is_admin and not next_is_admin
        deactivates_admin = user.is_admin and data.is_active is False
        if is_self_update and (demotes_admin or deactivates_admin):
            raise ValidationError("You cannot remove your own admin access")
        if demotes_admin or deactivates_admin:
            active_admin_count = await self.user_repository.count_active_admins()
            if active_admin_count <= 1:
                raise ValidationError("Cannot remove the last active admin user")

        if next_role != user.role:
            changes["role"] = {"old": user.role.value, "new": next_role.value}
            user.role = next_role

        if next_is_admin != user.is_admin:
            changes["is_admin"] = {"old": user.is_admin, "new": next_is_admin}
            user.is_admin = next_is_admin

        if data.is_active is not None and data.is_active != user.is_active:
            if is_self_update and not data.is_active:
                raise ValidationError("You cannot deactivate your own account")
            changes["is_active"] = {"old": user.is_active, "new": data.is_active}
            user.is_active = data.is_active

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
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        )
