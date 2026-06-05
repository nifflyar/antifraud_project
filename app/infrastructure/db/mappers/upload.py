from app.domain.upload.entity import Upload
from app.domain.upload.vo import UploadId, UploadStatus
from app.domain.user.vo import UserId
from app.infrastructure.db.models.upload import UploadModel


class UploadMapper:
    @staticmethod
    def to_domain(model: UploadModel) -> Upload:
        return Upload(
            id=model.id,
            filename=model.filename,
            filepath=model.filepath,
            uploaded_by_user_id=model.uploaded_by_user_id,
            uploaded_at=model.uploaded_at,
            status=model.status,
        )

    @staticmethod
    def to_model(upload: Upload) -> UploadModel:
        return UploadModel(
            id=upload.id,
            filename=upload.filename,
            filepath=upload.filepath,
            uploaded_by_user_id=upload.uploaded_by_user_id,
            uploaded_at=upload.uploaded_at,
            status=upload.status,
        )
