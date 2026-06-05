from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.scoring.vo import ScoringJobId, ScoringStatus
from app.domain.upload.vo import UploadId


@dataclass
class ScoringJob:
    """Сущность задачи скоринга."""

    id: ScoringJobId
    upload_id: UploadId
    status: ScoringStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @classmethod
    def create(cls, job_id: ScoringJobId, upload_id: UploadId) -> "ScoringJob":
        from datetime import datetime, UTC
        return cls(
            id=job_id,
            upload_id=upload_id,
            status=ScoringStatus.PENDING,
            started_at=datetime.now(UTC),
        )

    def mark_running(self) -> None:
        self.status = ScoringStatus.RUNNING

    def mark_done(self) -> None:
        from datetime import datetime, UTC
        self.status = ScoringStatus.DONE
        self.finished_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        from datetime import datetime, UTC
        self.status = ScoringStatus.FAILED
        self.finished_at = datetime.now(UTC)
        self.error_message = error
