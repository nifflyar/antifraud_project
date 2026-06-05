from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class DashboardSummaryResponse(BaseModel):
    total_passengers: int
    high_risk_count: int
    critical_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    high_risk_pct: float
    critical_risk_pct: float
    medium_risk_pct: float
    low_risk_pct: float
    share_suspicious_ops: float
    top_risk_channel: Optional[str] = None
    top_risk_terminal: Optional[str] = None

class RiskTrendItem(BaseModel):
    date: datetime
    total_ops: int
    highrisk_ops: int
    critical_ops: int = 0
    share: float

class RiskTrendResponse(BaseModel):
    items: List[RiskTrendItem]

class RiskConcentrationItem(BaseModel):
    dimension_value: str
    total_ops: int
    highrisk_ops: int
    share_highrisk_ops: float
    lift_vs_base: float

class RiskConcentrationResponse(BaseModel):
    dimension_type: str
    items: List[RiskConcentrationItem]

class RiskStatsResponse(BaseModel):
    """Period-based risk statistics."""
    period: str
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    total_passengers: int
    total_ops: int
    critical_ops: int
    high_ops: int
    medium_ops: int
    low_ops: int
    critical_pct: float
    high_pct: float
    medium_pct: float
    low_pct: float
