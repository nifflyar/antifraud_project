from dishka import Provider

from .auth import AuthInteractorProvider
from .user import UserInteractorProvider
from .audit import AuditInteractorProvider
from .etl import EtlProvider
from .upload import UploadInteractorProvider
from .scoring import ScoringInteractorProvider
from .dashboard import DashboardInteractorProvider
from .passenger import PassengerInteractorProvider
from .operations import OperationsInteractorProvider
from .reports import ReportsInteractorProvider

interactor_providers: list[type[Provider]] = [
    AuthInteractorProvider,
    UserInteractorProvider,
    AuditInteractorProvider,
    EtlProvider,
    UploadInteractorProvider,
    ScoringInteractorProvider,
    DashboardInteractorProvider,
    PassengerInteractorProvider,
    OperationsInteractorProvider,
    ReportsInteractorProvider,
]

__all__ = [
    "AuthInteractorProvider",
    "UserInteractorProvider",
    "AuditInteractorProvider",
    "EtlProvider",
    "UploadInteractorProvider",
    "ScoringInteractorProvider",
    "DashboardInteractorProvider",
    "PassengerInteractorProvider",
    "interactor_providers",
]
