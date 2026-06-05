from dishka import make_async_container

from app.infrastructure.config import Config
from app.infrastructure.di.db import DBProvider
from app.infrastructure.di.auth import AuthProvider
from app.infrastructure.di.audit import AuditProvider
from app.infrastructure.di.ml import MlProvider
from app.infrastructure.di.config import ConfigProvider
from app.infrastructure.di.interactors import interactor_providers


def setup_dishka_container(config: Config):
    """
    Setup Dishka async DI container with all providers.

    Config is provided via ConfigProvider which makes it available to all other
    providers that declare it as a parameter using Dishka's dependency resolution.
    """
    return make_async_container(
        ConfigProvider(config),
        DBProvider(),
        AuthProvider(),
        AuditProvider(),
        MlProvider(),
        *[p() for p in interactor_providers],
    )