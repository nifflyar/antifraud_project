from dishka import Provider, Scope, provide

from app.application.dashboard.get_summary import GetDashboardSummaryInteractor
from app.application.dashboard.get_risk_trend import GetRiskTrendInteractor
from app.application.dashboard.get_risk_concentration import GetRiskConcentrationInteractor
from app.application.dashboard.get_risk_stats import GetRiskStatsInteractor
from app.domain.passenger.repository import IPassengerRepository
from app.domain.transaction.repository import ITransactionRepository
from app.domain.risk.repository import IRiskConcentrationRepository

class DashboardInteractorProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_dashboard_summary(
        self,
        passenger_repo: IPassengerRepository,
        transaction_repo: ITransactionRepository,
        risk_repo: IRiskConcentrationRepository,
    ) -> GetDashboardSummaryInteractor:
        return GetDashboardSummaryInteractor(
            passenger_repo=passenger_repo,
            transaction_repo=transaction_repo,
            risk_repo=risk_repo,
        )

    @provide(scope=Scope.REQUEST)
    def get_risk_trend(
        self,
        transaction_repo: ITransactionRepository,
    ) -> GetRiskTrendInteractor:
        return GetRiskTrendInteractor(transaction_repo=transaction_repo)

    @provide(scope=Scope.REQUEST)
    def get_risk_concentration(
        self,
        risk_repo: IRiskConcentrationRepository,
        transaction_repo: ITransactionRepository,
    ) -> GetRiskConcentrationInteractor:
        return GetRiskConcentrationInteractor(
            risk_repo=risk_repo,
            transaction_repo=transaction_repo,
        )

    @provide(scope=Scope.REQUEST)
    def get_risk_stats(
        self,
        passenger_repo: IPassengerRepository,
        transaction_repo: ITransactionRepository,
    ) -> GetRiskStatsInteractor:
        return GetRiskStatsInteractor(
            passenger_repo=passenger_repo,
            transaction_repo=transaction_repo,
        )
