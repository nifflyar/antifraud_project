"""DI-провайдер для ETL-пайплайна."""
from dishka import Provider, Scope, provide

from app.application.etl.pipeline import EtlPipeline
from app.application.common.transaction import TransactionManager
from app.application.services.audit import AuditService
from app.domain.passenger.repository import IPassengerRepository
from app.domain.transaction.repository import ITransactionRepository
from app.domain.upload.repository import IUploadRepository


class EtlProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_etl_pipeline(
        self,
        transaction_repo: ITransactionRepository,
        passenger_repo: IPassengerRepository,
        upload_repo: IUploadRepository,
        audit_service: AuditService,
        transaction_manager: TransactionManager,
    ) -> EtlPipeline:
        return EtlPipeline(
            transaction_repo=transaction_repo,
            passenger_repo=passenger_repo,
            upload_repo=upload_repo,
            audit_service=audit_service,
            transaction_manager=transaction_manager,
        )
