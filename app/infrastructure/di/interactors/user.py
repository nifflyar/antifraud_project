from dishka import Provider, Scope, provide

from app.application.user.get_me import GetUserProfileInteractor
from app.application.user.list_users import ListUsersInteractor
from app.application.user.get_user_by_id import GetUserByIdInteractor
from app.application.user.update_user import UpdateUserInteractor
from app.application.user.delete_user import DeleteUserInteractor
from app.application.services.audit import AuditService
from app.domain.user.repository import IUserRepository


class UserInteractorProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_user_profile_interactor(
        self,
        user_repository: IUserRepository,
    ) -> GetUserProfileInteractor:
        return GetUserProfileInteractor(user_repository)

    @provide
    def provide_list_users_interactor(
        self,
        user_repository: IUserRepository,
    ) -> ListUsersInteractor:
        return ListUsersInteractor(user_repository)

    @provide
    def provide_get_user_by_id_interactor(
        self,
        user_repository: IUserRepository,
    ) -> GetUserByIdInteractor:
        return GetUserByIdInteractor(user_repository)

    @provide
    def provide_update_user_interactor(
        self,
        user_repository: IUserRepository,
        audit_service: AuditService,
    ) -> UpdateUserInteractor:
        return UpdateUserInteractor(user_repository, audit_service)

    @provide
    def provide_delete_user_interactor(
        self,
        user_repository: IUserRepository,
        audit_service: AuditService,
    ) -> DeleteUserInteractor:
        return DeleteUserInteractor(user_repository, audit_service)
