from dataclasses import dataclass

from app.application.common.interactor import Interactor
from app.domain.upload.repository import IUploadRepository
from app.domain.upload.vo import UploadId


@dataclass
class GetUploadInputDTO:
    upload_id: int


@dataclass
class GetUploadOutputDTO:
    id: int
    filename: str
    status: str
    uploaded_at: str
    uploaded_by_user_id: int | None


class GetUploadInteractor(Interactor[GetUploadInputDTO, GetUploadOutputDTO]):
    def __init__(self, upload_repository: IUploadRepository) -> None:
        self.upload_repository = upload_repository

    async def __call__(self, data: GetUploadInputDTO) -> GetUploadOutputDTO:
        upload = await self.upload_repository.get_by_id(UploadId(data.upload_id))
        
        if not upload:
            raise ValueError(f"Upload with id {data.upload_id} not found")

        return GetUploadOutputDTO(
            id=int(upload.id.value),
            filename=upload.filename,
            status=str(upload.status.value),
            uploaded_at=upload.uploaded_at.isoformat(),
            uploaded_by_user_id=int(upload.uploaded_by_user_id.value) if upload.uploaded_by_user_id else None,
        )
