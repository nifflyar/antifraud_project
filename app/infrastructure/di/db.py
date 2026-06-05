from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.application.common.transaction import TransactionManager
from app.domain.audit.repository import IAuditLogRepository
from app.domain.auth import RefreshSessionRepository
from app.domain.user.repository import IUserRepository
from app.domain.upload.repository import IUploadRepository
from app.domain.transaction.repository import ITransactionRepository
from app.domain.passenger.repository import IPassengerRepository
from app.domain.passenger.feature_repository import IPassengerFeatureRepository
from app.domain.passenger.score_repository import IPassengerScoreRepository
from app.domain.risk.repository import IRiskConcentrationRepository
from app.domain.scoring.repository import IScoringJobRepository
from app.infrastructure.config import Config
from app.infrastructure.db.factory import create_session_maker
from app.infrastructure.db.holder import HolderDao
from app.infrastructure.db.transaction import TransactionManagerImpl


class DBProvider(Provider):
    scope = Scope.APP

    @provide(scope=Scope.APP)
    def get_engine(self, config: Config) -> AsyncEngine:
        """
        Provide AsyncEngine - created lazily without connection validation.

        Using create_async_engine with echo_pool_connect=False to avoid
        premature connection attempts during provider initialization.
        """
        return create_async_engine(
            config.postgres.get_url(),
            echo=config.postgres.echo,
            pool_size=config.postgres.pool_size,
            pool_timeout=config.postgres.pool_timeout,
            pool_recycle=config.postgres.pool_recycle,
            max_overflow=config.postgres.max_overflow,
            pool_pre_ping=config.postgres.pool_pre_ping,
            echo_pool=config.postgres.echo_pool,
            # Prevent connection validation during engine creation
            connect_args={"server_settings": {"application_name": "antifrode"}},
        )

    @provide(scope=Scope.APP)
    def get_session_maker(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        return create_session_maker(engine)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[AsyncSession]:
        async with session_maker() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    async def get_holder_dao(
        self,
        session: AsyncSession,
    ) -> HolderDao:
        return HolderDao(session)

    @provide(scope=Scope.REQUEST)
    async def get_transaction_manager(
        self,
        session: AsyncSession,
    ) -> TransactionManager:
        return TransactionManagerImpl(session)

    @provide(scope=Scope.REQUEST)
    async def get_user_repository(
        self,
        holder_dao: HolderDao,
    ) -> IUserRepository:
        return holder_dao.user_repo

    @provide(scope=Scope.REQUEST)
    async def get_refresh_session_repository(
        self,
        holder_dao: HolderDao,
    ) -> RefreshSessionRepository:
        return holder_dao.refresh_session_repo

    @provide(scope=Scope.REQUEST)
    async def get_audit_log_repository(
        self,
        holder_dao: HolderDao,
    ) -> IAuditLogRepository:
        return holder_dao.audit_log_repo

    @provide(scope=Scope.REQUEST)
    async def get_upload_repository(
        self,
        holder_dao: HolderDao,
    ) -> IUploadRepository:
        return holder_dao.upload_repo

    @provide(scope=Scope.REQUEST)
    async def get_transaction_repository(
        self,
        holder_dao: HolderDao,
    ) -> ITransactionRepository:
        return holder_dao.transaction_repo

    @provide(scope=Scope.REQUEST)
    async def get_passenger_repository(
        self,
        holder_dao: HolderDao,
    ) -> IPassengerRepository:
        return holder_dao.passenger_repo

    @provide(scope=Scope.REQUEST)
    async def get_passenger_feature_repository(
        self,
        holder_dao: HolderDao,
    ) -> IPassengerFeatureRepository:
        return holder_dao.passenger_feature_repo

    @provide(scope=Scope.REQUEST)
    async def get_passenger_score_repository(
        self,
        holder_dao: HolderDao,
    ) -> IPassengerScoreRepository:
        return holder_dao.passenger_score_repo

    @provide(scope=Scope.REQUEST)
    async def get_risk_concentration_repository(
        self,
        holder_dao: HolderDao,
    ) -> IRiskConcentrationRepository:
        return holder_dao.risk_concentration_repo

    @provide(scope=Scope.REQUEST)
    async def get_scoring_job_repository(
        self,
        holder_dao: HolderDao,
    ) -> IScoringJobRepository:
        return holder_dao.scoring_job_repo
