from app.domain.upload.entity import Upload
from app.domain.upload.vo import UploadId, UploadStatus
from app.domain.user.vo import UserId
from app.infrastructure.db.models.upload import UploadModel


class UploadMapper:
    @staticmethod
    def to_domain(model: UploadModel) -> Upload:
        upload_id = model.id if isinstance(model.id, UploadId) else UploadId(int(model.id))
        return Upload(
            id=upload_id,
            filename=model.filename,
            filepath=model.filepath,
            uploaded_by_user_id=model.uploaded_by_user_id,
            uploaded_at=model.uploaded_at,
            status=model.status,
            error_message=model.error_message,
        )

    @staticmethod
    def to_model(upload: Upload) -> UploadModel:
        upload_id = upload.id.value if isinstance(upload.id, UploadId) else int(upload.id)
        return UploadModel(
            id=upload_id,
            filename=upload.filename,
            filepath=upload.filepath,
            uploaded_by_user_id=upload.uploaded_by_user_id,
            uploaded_at=upload.uploaded_at,
            status=upload.status,
            error_message=upload.error_message,
        )
