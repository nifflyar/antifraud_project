import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any

from app.application.common.interactor import Interactor
from app.application.common.transaction import TransactionManager
from app.application.services.audit import AuditService
from app.domain.upload.entity import Upload
from app.domain.upload.repository import IUploadRepository
from app.domain.upload.vo import UploadId, UploadStatus
from app.domain.user.vo import UserId

logger = logging.getLogger(__name__)


@dataclass
class CreateUploadInputDTO:
    filename: str
    filepath: str
    user_id: UserId


@dataclass
class CreateUploadOutputDTO:
    id: int
    filename: str
    status: str
    uploaded_at: str


class CreateUploadInteractor(Interactor[CreateUploadInputDTO, CreateUploadOutputDTO]):
    """Создаёт новую запись о загрузке в БД и логирует начало загрузки."""

    def __init__(
        self,
        upload_repository: IUploadRepository,
        audit_service: AuditService,
        transaction_manager: TransactionManager,
    ) -> None:
        self.upload_repository = upload_repository
        self.audit_service = audit_service
        self.transaction_manager = transaction_manager

    async def __call__(self, data: CreateUploadInputDTO) -> CreateUploadOutputDTO:
        # Создаем сущность загрузки
        # ID генерируется БД, поэтому пока 0.
        # В реальном коде, лучше создать метод `get_next_id()` если нужно вернуть сразу
        # Или использовать UUID/snowflake для ID загрузки
        # В нашей модели `UploadModel` id = int, autoincrement.
        # Поэтому мы сначала сохраняем, потом получаем.
        
        # NOTE: SQLAlchemy flush даст нам ID
        upload = Upload(
            id=0, # type: ignore # Временный ID, обновится после flush
            filename=data.filename,
            filepath=data.filepath,
            uploaded_by_user_id=data.user_id, # Передаем UserId объект
            uploaded_at=datetime.now(UTC),
            status=UploadStatus.PENDING,
        )

        await self.upload_repository.create_upload(upload)
        await self.transaction_manager.commit()
        
        # Получаем присвоенный ID (SQLAlchemy обновит объект внутри mapper/repo, если настроено,
        # но так как у нас ручной маппер, нам надо его забрать. 
        # Допустим, мы используем просто возврат как есть, 
        # Или нам нужно изменить логику `create_upload` чтобы он возвращал ID/Сущность.
        # В идеале `UploadModel` после `session.add(model)` и `session.flush()` имеет `model.id`.
        # Я исправлю `UploadRepositoryImpl.create_upload` чуть позже чтобы он устанавливал `upload.id = model.id`

        await self.audit_service.log_upload_started(
            upload_id=str(upload.id), user_id=data.user_id
        )
        await self.transaction_manager.commit()

        # Явно извлекаем int значения для DTO, чтобы IDE не ругалась на типы
        return CreateUploadOutputDTO(
            id=int(upload.id.value),
            filename=upload.filename,
            status=str(upload.status.value),
            uploaded_at=upload.uploaded_at.isoformat(),
        )
