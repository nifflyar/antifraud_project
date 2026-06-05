from enum import Enum
from dataclasses import dataclass

from app.domain.common.vo.integer import PositiveInteger

class DimensionType(str, Enum):
    CHANNEL = "channel"
    AGGREGATOR = "aggregator"
    TERMINAL = "terminal"
    CASHDESK = "cashdesk"
    POINT_OF_SALE = "point_of_sale"


class RiskConcentrationId(PositiveInteger):
    pass