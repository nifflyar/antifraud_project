from app.domain.auth import RefreshSession
from app.infrastructure.db.models.refresh_session import RefreshSessionModel


class RefreshSessionMapper:
    @staticmethod
    def to_domain(model: RefreshSessionModel) -> RefreshSession:
        return RefreshSession(
            token_hash=model.token_hash,
            user_id=model.user_id,
            expires_at=model.expires_at,
            created_at=model.created_at,
            revoked_at=model.revoked_at,
        )

    @staticmethod
    def to_model(session: RefreshSession) -> RefreshSessionModel:
        return RefreshSessionModel(
            token_hash=session.token_hash,
            user_id=session.user_id,
            expires_at=session.expires_at,
            created_at=session.created_at,
            revoked_at=session.revoked_at,
        )
