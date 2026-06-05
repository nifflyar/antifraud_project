from datetime import datetime

from sqlalchemy import TIMESTAMP, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.upload.vo import UploadId, UploadStatus
from app.domain.user.vo import UserId

from .base import BaseORMModel
from .types.entities import UploadIdType, UserIdType


class UploadModel(BaseORMModel):
    __tablename__ = "uploads"

    id: Mapped[UploadId] = mapped_column(UploadIdType, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(1024), nullable=False)
    uploaded_by_user_id: Mapped[UserId] = mapped_column(UserIdType, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    status: Mapped[UploadStatus] = mapped_column(
        Enum(UploadStatus, name="uploadstatus", create_type=True),
        nullable=False,
        default=UploadStatus.PENDING,
    )
