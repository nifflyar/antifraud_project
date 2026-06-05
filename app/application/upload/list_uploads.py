from dataclasses import dataclass

from app.application.common.interactor import Interactor
from app.domain.upload.repository import IUploadRepository


@dataclass
class ListUploadsInputDTO:
    limit: int = 20
    offset: int = 0


@dataclass
class UploadListItemDTO:
    id: int
    filename: str
    status: str
    uploaded_at: str
    uploaded_by_user_id: int | None


@dataclass
class ListUploadsOutputDTO:
    items: list[UploadListItemDTO]
    limit: int
    offset: int


class ListUploadsInteractor(Interactor[ListUploadsInputDTO, ListUploadsOutputDTO]):
    def __init__(self, upload_repository: IUploadRepository) -> None:
        self.upload_repository = upload_repository

    async def __call__(self, data: ListUploadsInputDTO) -> ListUploadsOutputDTO:
        # Validate limits
        if data.limit > 100:
            data.limit = 100
        if data.limit < 1:
            data.limit = 1

        uploads = await self.upload_repository.get_all(
            limit=data.limit, offset=data.offset
        )

        items = [
            UploadListItemDTO(
                id=int(u.id.value),
                filename=u.filename,
                status=str(u.status.value),
                uploaded_at=u.uploaded_at.isoformat(),
                uploaded_by_user_id=int(u.uploaded_by_user_id.value) if u.uploaded_by_user_id else None,
            )
            for u in uploads
        ]

        return ListUploadsOutputDTO(
            items=items,
            limit=data.limit,
            offset=data.offset,
        )
