from app.domain.scoring.entity import ScoringJob
from app.domain.scoring.vo import ScoringJobId
from app.domain.upload.vo import UploadId
from app.infrastructure.db.models.scoring_job import ScoringJobModel


class ScoringJobMapper:
    """Маппер для преобразования между ScoringJob (domain) и ScoringJobModel (DB)."""

    @staticmethod
    def to_domain(model: ScoringJobModel) -> ScoringJob:
        return ScoringJob(
            id=ScoringJobId(model.id),
            upload_id=model.upload_id,
            status=model.status,
            started_at=model.started_at,
            finished_at=model.finished_at,
            error_message=model.error_message,
        )

    @staticmethod
    def to_model(entity: ScoringJob) -> ScoringJobModel:
        return ScoringJobModel(
            id=entity.id.value,
            upload_id=entity.upload_id.value,
            status=entity.status,
            started_at=entity.started_at,
            finished_at=entity.finished_at,
            error_message=entity.error_message,
        )
