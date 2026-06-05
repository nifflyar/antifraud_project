from abc import ABC, abstractmethod
from app.domain.upload.entity import Upload
from app.domain.upload.vo import UploadId


class IUploadRepository(ABC):

    @abstractmethod
    async def get_by_id(self, upload_id: UploadId) -> Upload | None: ...

    @abstractmethod
    async def get_all(self, limit: int = 20, offset: int = 0) -> list[Upload]: ...

    @abstractmethod
    async def create_upload(self, upload: Upload) -> None: ...

    @abstractmethod
    async def update_upload(self, upload: Upload) -> None: ...

    @abstractmethod
    async def delete_upload(self, upload_id: UploadId) -> None: ...