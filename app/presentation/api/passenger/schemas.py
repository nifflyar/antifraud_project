from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional
from app.domain.passenger.vo import RiskBand

class PassengerScoreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    rule_score: float
    ml_score: float
    final_score: float
    risk_band: RiskBand
    top_reasons: List[str]
    seat_blocking_flag: bool
    is_manual: bool
    scored_at: Optional[datetime]

class PassengerFeaturesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_tickets: int
    refund_cnt: int
    refund_share: float
    night_tickets: int
    night_share: float
    max_tickets_month: int
    max_tickets_same_depday: int
    refund_close_ratio: float
    tickets_per_train_peak: float
    fio_fake_score_max: float
    late_refunds: int = 0
    late_refund_share: float = 0.0
    very_late_refunds: int = 0
    very_late_refund_share: float = 0.0
    quick_refunds: int = 0
    quick_refund_share: float = 0.0
    activity_days: int = 1
    suspicious_refund_pattern_cnt: int = 0
    refund_amount_diversity: float = 1.0
    seat_blocking_flag: bool = False

class PassengerListItemSchema(BaseModel):
    id: str
    fio_clean: str
    fake_fio_score: float
    last_seen_at: datetime
    risk_band: RiskBand
    final_score: float

class PassengerListResponse(BaseModel):
    items: List[PassengerListItemSchema]
    total: int
    limit: int
    offset: int

class PassengerIdentitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    iin: Optional[str] = None
    doc_no: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    raw_fio: Optional[str] = None
    channels: List[str] = Field(default_factory=list)
    aggregators: List[str] = Field(default_factory=list)
    terminals: List[str] = Field(default_factory=list)
    branches: List[str] = Field(default_factory=list)
    sale_users: List[str] = Field(default_factory=list)
    carriers: List[str] = Field(default_factory=list)
    tariff_types: List[str] = Field(default_factory=list)
    service_classes: List[str] = Field(default_factory=list)
    routes: List[str] = Field(default_factory=list)
    train_numbers: List[str] = Field(default_factory=list)
    distinct_iin_count: int = 0
    distinct_doc_count: int = 0
    distinct_phone_count: int = 0
    distinct_terminal_count: int = 0
    distinct_route_count: int = 0
    first_operation_at: Optional[datetime] = None
    last_operation_at: Optional[datetime] = None

class PassengerProfileResponse(BaseModel):
    id: str
    fio_clean: str
    fake_fio_score: float
    first_seen_at: datetime
    last_seen_at: datetime
    identity: Optional[PassengerIdentitySchema] = None
    features: Optional[PassengerFeaturesSchema]
    score: Optional[PassengerScoreSchema]

class PassengerTransactionSchema(BaseModel):
    id: str
    op_type: str
    op_datetime: datetime
    dep_datetime: Optional[datetime]
    train_no: Optional[str]
    amount: float
    fee: float
    channel: Optional[str]
    aggregator: Optional[str]
    terminal: Optional[str]
    cashdesk: Optional[str]
    point_of_sale: Optional[str]
    order_no: Optional[str]
    ticket_no: Optional[str]
    tariff_type: Optional[str]
    service_class: Optional[str]
    dep_station: Optional[str]
    arr_station: Optional[str]
    route: Optional[str]
    fio: Optional[str]
    iin: Optional[str]
    doc_no: Optional[str]
    phone: Optional[str]
    gender: Optional[str]
    branch: Optional[str]
    sale_user: Optional[str]
    carrier: Optional[str]
    settlement_type: Optional[str]

class PassengerTransactionsResponse(BaseModel):
    items: List[PassengerTransactionSchema]
    total: int
    limit: int
    offset: int

class RiskOverrideRequest(BaseModel):
    new_risk_band: RiskBand
    reason: str
