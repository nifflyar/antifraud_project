from dishka import Provider, Scope, provide

from app.application.scoring.process_results import ProcessScoringResultsInteractor
from app.application.scoring.run_scoring import RunScoringInteractor
from app.application.scoring.get_scoring_status import GetScoringStatusInteractor
from app.application.common.transaction import TransactionManager
from app.domain.passenger.feature_repository import IPassengerFeatureRepository
from app.domain.passenger.score_repository import IPassengerScoreRepository
from app.domain.scoring.repository import IScoringJobRepository
from app.domain.upload.repository import IUploadRepository
from app.domain.transaction.repository import ITransactionRepository
from app.domain.risk.repository import IRiskConcentrationRepository
from app.infrastructure.ml_client import MlServiceClient


class ScoringInteractorProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_process_scoring_results(
        self,
        ml_client: MlServiceClient,
        feature_repo: IPassengerFeatureRepository,
        score_repo: IPassengerScoreRepository,
        scoring_job_repo: IScoringJobRepository,
        transaction_repo: ITransactionRepository,
        risk_repo: IRiskConcentrationRepository,
        transaction_manager: TransactionManager,
    ) -> ProcessScoringResultsInteractor:
        return ProcessScoringResultsInteractor(
            ml_client=ml_client,
            feature_repo=feature_repo,
            score_repo=score_repo,
            scoring_job_repo=scoring_job_repo,
            transaction_repo=transaction_repo,
            risk_repo=risk_repo,
            transaction_manager=transaction_manager,
        )

    @provide(scope=Scope.REQUEST)
    def get_run_scoring(
        self,
        upload_repo: IUploadRepository,
        scoring_job_repo: IScoringJobRepository,
        transaction_manager: TransactionManager,
    ) -> RunScoringInteractor:
        return RunScoringInteractor(
            upload_repo=upload_repo,
            scoring_job_repo=scoring_job_repo,
            transaction_manager=transaction_manager,
        )

    @provide(scope=Scope.REQUEST)
    def get_scoring_status(
        self,
        scoring_job_repo: IScoringJobRepository,
    ) -> GetScoringStatusInteractor:
        return GetScoringStatusInteractor(
            scoring_job_repo=scoring_job_repo,
        )
