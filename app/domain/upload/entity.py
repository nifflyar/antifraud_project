from dataclasses import dataclass
from datetime import datetime, UTC



from app.domain.upload.vo import UploadId, UploadStatus
from app.domain.user.vo import UserId


@dataclass
class Upload:
    id: UploadId
    filename: str
    filepath: str
    uploaded_by_user_id: UserId
    uploaded_at: datetime
    status: UploadStatus


    def mark_processing(self) -> None:
        if self.status != UploadStatus.PENDING:
            raise ValueError(f"Cannot start processing: status is {self.status}")
        self.status = UploadStatus.PROCESSING

    def mark_done(self) -> None:
        if self.status not in (UploadStatus.PROCESSING, UploadStatus.PENDING):
            raise ValueError(f"Cannot complete: status is {self.status}")
        self.status = UploadStatus.DONE

    def mark_failed(self) -> None:
        self.status = UploadStatus.FAILED

    def is_complete(self) -> bool:
        return self.status == UploadStatus.DONE


    @classmethod
    def create(cls, upload_id: str, filename: str,
               filepath: str, uploaded_by_user_id: str) -> "Upload":
        return cls(
            id=UploadId(upload_id),
            filename=filename,
            filepath=filepath,
            uploaded_by_user_id=UserId(uploaded_by_user_id),
            uploaded_at=datetime.now(UTC),
            status=UploadStatus.PENDING,
        )