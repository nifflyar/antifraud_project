from sqlalchemy import select, update

from app.domain.upload.entity import Upload
from app.domain.upload.repository import IUploadRepository
from app.domain.upload.vo import UploadId
from app.infrastructure.db.mappers.upload import UploadMapper
from app.infrastructure.db.models.upload import UploadModel
from app.infrastructure.db.repos.base import BaseSQLAlchemyRepo


class UploadRepositoryImpl(IUploadRepository, BaseSQLAlchemyRepo):

    async def get_by_id(self, upload_id: UploadId) -> Upload | None:
        stmt = select(UploadModel).where(UploadModel.id == upload_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UploadMapper.to_domain(model) if model else None

    async def get_all(self, limit: int = 20, offset: int = 0) -> list[Upload]:
        stmt = (
            select(UploadModel)
            .order_by(UploadModel.uploaded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [UploadMapper.to_domain(m) for m in result.scalars().all()]

    async def create_upload(self, upload: Upload) -> None:
        model = UploadMapper.to_model(upload)
        # Если id = 0 или None (как временный маркер), SQLAlchemy игнорирует это при autoflush/autoincrement,
        # но безопаснее удалить его из state перед add:
        if hasattr(model, 'id') and model.id == 0:
            del model.id
        self._session.add(model)
        await self._session.flush()
        upload.id = model.id

    async def update_upload(self, upload: Upload) -> None:
        stmt = (
            update(UploadModel)
            .where(UploadModel.id == upload.id)
            .values(
                status=upload.status,
                filename=upload.filename,
                filepath=upload.filepath,
            )
        )
        await self._session.execute(stmt)

    async def delete_upload(self, upload_id: UploadId) -> None:
        from sqlalchemy import delete
        stmt = delete(UploadModel).where(UploadModel.id == upload_id)
        await self._session.execute(stmt)
