from sqlalchemy import select, func
from datetime import datetime

from app.domain.audit.entity import AuditLog
from app.domain.audit.repository import IAuditLogRepository
from app.domain.user.vo import UserId
from app.infrastructure.db.models.audit import AuditLogModel
from app.infrastructure.db.repos.base import BaseSQLAlchemyRepo


class AuditLogRepositoryImpl(IAuditLogRepository, BaseSQLAlchemyRepo):
    async def create_audit_log(self, log: AuditLog) -> None:
        model = AuditLogModel(
            id=log.id,
            user_id=log.user_id.value if log.user_id else None,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            meta=log.meta,
            created_at=log.created_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, log_id: str) -> AuditLog | None:
        stmt = select(AuditLogModel).where(AuditLogModel.id == log_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_all(self, limit: int = 100, offset: int = 0) -> tuple[list[AuditLog], int]:
        # Get total count
        count_stmt = select(func.count(AuditLogModel.id))
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        # Get paginated results
        stmt = (
            select(AuditLogModel)
            .limit(limit)
            .offset(offset)
            .order_by(AuditLogModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models], total

    async def get_all_by_user(
        self, user_id: UserId, limit: int = 100
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.user_id == user_id.value)
            .limit(limit)
            .order_by(AuditLogModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_all_by_entity(
        self, entity_type: str, entity_id: str
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(
                (AuditLogModel.entity_type == entity_type)
                & (AuditLogModel.entity_id == entity_id)
            )
            .order_by(AuditLogModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_all_by_action(
        self, action: str, limit: int = 100
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.action == action)
            .limit(limit)
            .order_by(AuditLogModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_all_by_date_range(
        self, date_from: str, date_to: str, limit: int = 100
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(
                (AuditLogModel.created_at >= date_from)
                & (AuditLogModel.created_at <= date_to)
            )
            .limit(limit)
            .order_by(AuditLogModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    @staticmethod
    def _to_domain(model: AuditLogModel) -> AuditLog:
        return AuditLog(
            id=model.id,
            user_id=UserId(model.user_id) if model.user_id else None,
            action=model.action,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            created_at=model.created_at,
            meta=model.meta or {},
        )
