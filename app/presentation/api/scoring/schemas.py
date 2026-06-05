from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.scoring.vo import ScoringStatus


class ScoringRunRequest(BaseModel):
    upload_id: int


class ScoringRunResponse(BaseModel):
    job_id: UUID
    status: ScoringStatus
    started_at: datetime


class ScoringStatusResponse(BaseModel):
    job_id: UUID
    upload_id: int
    status: ScoringStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
