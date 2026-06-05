from enum import Enum
from dataclasses import dataclass

from app.domain.common.vo.integer import PositiveInteger


class TransactionId(PositiveInteger):
    pass


class OperationType(str, Enum):
    SALE = "sale"
    REFUND = "refund"
    REDEEM = "redeem"
    OTHER = "other"


class DataSource(str, Enum):
    EXCEL_UPLOAD = "excel_upload"
    API = "api"

