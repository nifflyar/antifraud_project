from dishka import Provider, Scope, provide

from app.application.passenger.list_passengers import ListPassengersInteractor
from app.application.passenger.get_passenger_profile import GetPassengerProfileInteractor
from app.application.passenger.get_passenger_transactions import GetPassengerTransactionsInteractor
from app.application.passenger.get_risk_stats import GetPassengerRiskStatsInteractor
from app.domain.passenger.repository import IPassengerRepository
from app.domain.passenger.score_repository import IPassengerScoreRepository
from app.domain.transaction.repository import ITransactionRepository
from app.application.passenger.override_risk import OverridePassengerRiskInteractor
from app.application.services.audit import AuditService
from app.application.common.transaction import TransactionManager


class PassengerInteractorProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def list_passengers(self, repo: IPassengerRepository) -> ListPassengersInteractor:
        return ListPassengersInteractor(repo)

    @provide
    def get_profile(self, repo: IPassengerRepository) -> GetPassengerProfileInteractor:
        return GetPassengerProfileInteractor(repo)

    @provide
    def get_transactions(self, repo: ITransactionRepository) -> GetPassengerTransactionsInteractor:
        return GetPassengerTransactionsInteractor(repo)

    @provide
    def override_risk(
        self,
        score_repo: IPassengerScoreRepository,
        audit_service: AuditService,
        transaction_manager: TransactionManager,
    ) -> OverridePassengerRiskInteractor:
        return OverridePassengerRiskInteractor(score_repo, audit_service, transaction_manager)

    @provide
    def get_risk_stats(self, repo: IPassengerRepository) -> GetPassengerRiskStatsInteractor:
        return GetPassengerRiskStatsInteractor(repo)
