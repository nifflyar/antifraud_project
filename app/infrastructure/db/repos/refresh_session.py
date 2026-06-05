from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.domain.auth import RefreshSession, RefreshSessionRepository
from app.infrastructure.db.mappers.refresh_session import RefreshSessionMapper
from app.infrastructure.db.models.refresh_session import RefreshSessionModel
from app.infrastructure.db.repos.base import BaseSQLAlchemyRepo


class RefreshSessionRepositoryImpl(RefreshSessionRepository, BaseSQLAlchemyRepo):
    async def get_session_by_token_hash(self, token_hash: str) -> RefreshSession | None:
        stmt = select(RefreshSessionModel).where(RefreshSessionModel.token_hash == token_hash)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return RefreshSessionMapper.to_domain(model) if model else None

    async def create_session(self, session: RefreshSession) -> RefreshSession:
        stmt = (
            insert(RefreshSessionModel)
            .values(
                token_hash=session.token_hash,
                user_id=session.user_id.value,
                expires_at=session.expires_at,
                created_at=session.created_at,
                revoked_at=session.revoked_at,
            )
            .returning(RefreshSessionModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        return RefreshSessionMapper.to_domain(model)

    async def revoke_session(
        self, token_hash: str, revoked_at: datetime
    ) -> RefreshSession | None:
        stmt = (
            update(RefreshSessionModel)
            .where(RefreshSessionModel.token_hash == token_hash)
            .where(RefreshSessionModel.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
            .returning(RefreshSessionModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return RefreshSessionMapper.to_domain(model) if model else None
