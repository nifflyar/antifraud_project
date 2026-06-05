from dishka import Provider, Scope, provide

from app.application.auth.login import LoginInteractor
from app.application.common.transaction import TransactionManager
from app.application.auth.logout import LogoutInteractor
from app.application.auth.refresh import RefreshInteractor
from app.application.auth.register import RegisterInteractor
from app.application.interfaces.auth import AuthService
from app.domain.auth import RefreshSessionRepository
from app.domain.user.repository import IUserRepository
from app.infrastructure.config import Config


class AuthInteractorProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_register_interactor(
        self,
        user_repository: IUserRepository,
        auth_service: AuthService,
        config: Config,
    ) -> RegisterInteractor:
        return RegisterInteractor(
            user_repository=user_repository,
            auth_service=auth_service,
            admin_emails=set(config.auth.admin_emails),
        )

    @provide
    def provide_login_interactor(
        self,
        user_repository: IUserRepository,
        refresh_session_repository: RefreshSessionRepository,
        auth_service: AuthService,
        config: Config,
        transaction_manager: TransactionManager,
    ) -> LoginInteractor:
        return LoginInteractor(
            user_repository=user_repository,
            refresh_session_repository=refresh_session_repository,
            auth_service=auth_service,
            transaction_manager=transaction_manager,
            admin_emails=set(config.auth.admin_emails),
            refresh_token_expire_days=config.auth.refresh_token_expire_days,
        )

    @provide
    def provide_refresh_interactor(
        self,
        user_repository: IUserRepository,
        refresh_session_repository: RefreshSessionRepository,
        auth_service: AuthService,
    ) -> RefreshInteractor:
        return RefreshInteractor(
            user_repository=user_repository,
            refresh_session_repository=refresh_session_repository,
            auth_service=auth_service,
        )

    @provide
    def provide_logout_interactor(
        self,
        refresh_session_repository: RefreshSessionRepository,
        auth_service: AuthService,
    ) -> LogoutInteractor:
        return LogoutInteractor(
            refresh_session_repository=refresh_session_repository,
            auth_service=auth_service,
        )
