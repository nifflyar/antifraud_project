from typing import Optional

from sqlalchemy import select

from app.domain.scoring.entity import ScoringJob
from app.domain.scoring.repository import IScoringJobRepository
from app.domain.scoring.vo import ScoringJobId
from app.infrastructure.db.mappers.scoring_job import ScoringJobMapper
from app.infrastructure.db.models.scoring_job import ScoringJobModel
from app.infrastructure.db.repos.base import BaseSQLAlchemyRepo


class ScoringJobRepositoryImpl(IScoringJobRepository, BaseSQLAlchemyRepo):
    """Реализация репозитория задач скоринга через SQLAlchemy."""

    async def get_by_id(self, job_id: ScoringJobId) -> Optional[ScoringJob]:
        stmt = select(ScoringJobModel).where(ScoringJobModel.id == job_id.value)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return ScoringJobMapper.to_domain(model) if model else None

    async def create(self, job: ScoringJob) -> None:
        model = ScoringJobMapper.to_model(job)
        self._session.add(model)
        await self._session.flush()

    async def update(self, job: ScoringJob) -> None:
        model = ScoringJobMapper.to_model(job)
        await self._session.merge(model)
        await self._session.flush()
