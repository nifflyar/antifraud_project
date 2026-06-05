from abc import ABC, abstractmethod
from typing import Optional

from app.domain.scoring.entity import ScoringJob
from app.domain.scoring.vo import ScoringJobId


class IScoringJobRepository(ABC):
    """Интерфейс репозитория для управления задачами скоринга."""

    @abstractmethod
    async def get_by_id(self, job_id: ScoringJobId) -> Optional[ScoringJob]:
        pass

    @abstractmethod
    async def create(self, job: ScoringJob) -> None:
        pass

    @abstractmethod
    async def update(self, job: ScoringJob) -> None:
        pass
