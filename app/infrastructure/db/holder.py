from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.repos import (
    RefreshSessionRepositoryImpl,
    UserRepositoryImpl,
    AuditLogRepositoryImpl,
    UploadRepositoryImpl,
    TransactionRepositoryImpl,
    PassengerRepositoryImpl,
    PassengerFeatureRepositoryImpl,
    PassengerScoreRepositoryImpl,
    RiskConcentrationRepositoryImpl,
    ScoringJobRepositoryImpl,
)


class HolderDao:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepositoryImpl(session)
        self.refresh_session_repo = RefreshSessionRepositoryImpl(session)
        self.audit_log_repo = AuditLogRepositoryImpl(session)
        self.upload_repo = UploadRepositoryImpl(session)
        self.transaction_repo = TransactionRepositoryImpl(session)
        self.passenger_repo = PassengerRepositoryImpl(session)
        self.passenger_feature_repo = PassengerFeatureRepositoryImpl(session)
        self.passenger_score_repo = PassengerScoreRepositoryImpl(session)
        self.risk_concentration_repo = RiskConcentrationRepositoryImpl(session)
        self.scoring_job_repo = ScoringJobRepositoryImpl(session)

