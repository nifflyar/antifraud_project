from dataclasses import dataclass
from typing import Any

from app.domain.transaction.vo import TransactionId, DataSource
from app.domain.upload.vo import UploadId



@dataclass(frozen=True)
class RawTransaction:
    id: TransactionId
    upload_id: UploadId
    source: DataSource
    raw_payload: dict[str, Any]

    @classmethod
    def create(cls, transaction_id: str, upload_id: UploadId,
               source: str, raw_row: dict) -> "RawTransaction":
        return cls(
            id=TransactionId(transaction_id),
            upload_id=upload_id,
            source=DataSource(source),
            raw_payload=raw_row,
        )