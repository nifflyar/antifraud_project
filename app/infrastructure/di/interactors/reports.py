from dishka import Provider, Scope, provide

from app.application.reports.export_suspicious_excel import ExportSuspiciousOperationsExcelInteractor
from app.application.reports.export_concentration_excel import ExportRiskConcentrationExcelInteractor
from app.application.reports.export_passenger_pdf import ExportPassengerProfilePdfInteractor
from app.application.reports.export_passengers_excel import ExportPassengersByRiskExcelInteractor
from app.domain.transaction.repository import ITransactionRepository
from app.domain.passenger.repository import IPassengerRepository
from app.domain.risk.repository import IRiskConcentrationRepository

class ReportsInteractorProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def export_suspicious(self, repo: ITransactionRepository) -> ExportSuspiciousOperationsExcelInteractor:
        return ExportSuspiciousOperationsExcelInteractor(repo)

    @provide
    def export_concentration(self, repo: IRiskConcentrationRepository) -> ExportRiskConcentrationExcelInteractor:
        return ExportRiskConcentrationExcelInteractor(repo)

    @provide
    def export_passenger_pdf(
        self,
        passenger_repo: IPassengerRepository,
        transaction_repo: ITransactionRepository
    ) -> ExportPassengerProfilePdfInteractor:
        return ExportPassengerProfilePdfInteractor(passenger_repo, transaction_repo)

    @provide
    def export_passengers_excel(self, repo: IPassengerRepository) -> ExportPassengersByRiskExcelInteractor:
        return ExportPassengersByRiskExcelInteractor(repo)
