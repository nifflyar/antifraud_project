from typing import Optional

from app.domain.scoring.entity import ScoringJob
from app.domain.scoring.repository import IScoringJobRepository
from app.domain.scoring.vo import ScoringJobId


class GetScoringStatusInteractor:
    """Интерэктор для получения статуса задачи скоринга."""

    def __init__(self, scoring_job_repo: IScoringJobRepository):
        self._scoring_job_repo = scoring_job_repo

    async def execute(self, job_id: str) -> Optional[ScoringJob]:
        from uuid import UUID
        try:
            jid = ScoringJobId(UUID(job_id))
        except ValueError:
            return None
            
        return await self._scoring_job_repo.get_by_id(jid)
