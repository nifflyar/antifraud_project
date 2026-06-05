from dataclasses import dataclass
from datetime import datetime

from app.domain.user.vo import UserId


@dataclass
class RefreshSession:
    token_hash: str
    user_id: UserId
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None

    def is_active_at(self, moment: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > moment
