from datetime import datetime
from uuid import UUID

from sqlalchemy import TIMESTAMP, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.domain.scoring.vo import ScoringJobId, ScoringStatus
from app.domain.upload.vo import UploadId

from .base import BaseORMModel
from .types.entities import UploadIdType


class ScoringJobModel(BaseORMModel):
    """Модель задачи скоринга для хранения в БД."""

    __tablename__ = "scoring_jobs"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    upload_id: Mapped[UploadId] = mapped_column(
        UploadIdType,
        ForeignKey("uploads.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ScoringStatus] = mapped_column(
        Enum(ScoringStatus, name="scoringstatus", create_type=True),
        nullable=False,
        default=ScoringStatus.PENDING,
    )
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    error_message: Mapped[str] = mapped_column(String(2048), nullable=True)
