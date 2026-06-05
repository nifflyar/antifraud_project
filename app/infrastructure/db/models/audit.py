from datetime import datetime

from sqlalchemy import TIMESTAMP, String, func, JSON, BigInteger, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import BaseORMModel


class AuditLogModel(BaseORMModel):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_created_at", "created_at"),
        Index("idx_audit_action_created", "action", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    meta: Mapped[dict] = mapped_column(JSON, nullable=True, default={})
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), index=True
    )
