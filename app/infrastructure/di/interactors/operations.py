from dishka import Provider, Scope, provide

from app.application.operations.list_suspicious import (
    ListOperationsInteractor,
    ListSuspiciousOperationsInteractor,
)
from app.domain.transaction.repository import ITransactionRepository

class OperationsInteractorProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def list_suspicious(self, repo: ITransactionRepository) -> ListSuspiciousOperationsInteractor:
        return ListSuspiciousOperationsInteractor(repo)

    @provide
    def list_operations(self, repo: ITransactionRepository) -> ListOperationsInteractor:
        return ListOperationsInteractor(repo)
