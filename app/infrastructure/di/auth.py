from dishka import Provider, Scope, provide

from app.application.interfaces.auth import AuthService
from app.infrastructure.auth import AuthServiceImpl
from app.infrastructure.config import Config


class AuthProvider(Provider):
    """Provider for authentication service"""
    scope = Scope.APP

    @provide(scope=Scope.APP)
    def provide_auth_service(self, config: Config) -> AuthService:
        """Provide the AuthService implementation with config dependency"""
        return AuthServiceImpl(config)
