from enum import Enum
from uuid import UUID

from app.domain.common.vo.base import BaseValueObject


class ScoringJobId(BaseValueObject[UUID]):
    pass


class ScoringStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
