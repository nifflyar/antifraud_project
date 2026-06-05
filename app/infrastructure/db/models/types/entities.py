import json
from typing import Any
from datetime import datetime

from sqlalchemy import BIGINT, JSON, TypeDecorator, Dialect

from app.domain.upload.vo import UploadId, UploadStatus
from app.domain.transaction.vo import TransactionId, OperationType
from app.domain.passenger.vo import PassengerId, RiskBand
from app.domain.passenger.entity import PassengerFeatures, PassengerScore
from app.domain.risk.vo import RiskConcentrationId, DimensionType
from app.domain.user.vo import UserId

from .base import VOType


class UploadIdType(VOType):
    impl = BIGINT
    vo_class = UploadId
    vo_raw = int
    cache_ok = True


class TransactionIdType(VOType):
    impl = BIGINT
    vo_class = TransactionId
    vo_raw = int
    cache_ok = True


class PassengerIdType(VOType):
    impl = BIGINT
    vo_class = PassengerId
    vo_raw = int
    cache_ok = True


class RiskConcentrationIdType(VOType):
    impl = BIGINT
    vo_class = RiskConcentrationId
    vo_raw = int
    cache_ok = True


class UserIdType(VOType):
    impl = BIGINT
    vo_class = UserId
    vo_raw = int
    cache_ok = True


class PassengerFeaturesType(TypeDecorator):
    """Custom type for serializing/deserializing PassengerFeatures to/from JSON"""
    impl = JSON
    cache_ok = True

    def process_bind_param(
        self, value: PassengerFeatures | None, dialect: Dialect
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        return {
            "total_tickets": value.total_tickets,
            "refund_cnt": value.refund_cnt,
            "refund_share": value.refund_share,
            "night_tickets": value.night_tickets,
            "night_share": value.night_share,
            "max_tickets_month": value.max_tickets_month,
            "max_tickets_same_depday": value.max_tickets_same_depday,
            "refund_close_ratio": value.refund_close_ratio,
            "tickets_per_train_peak": value.tickets_per_train_peak,
            "fio_fake_score_max": value.fio_fake_score_max,
        }

    def process_result_value(
        self, value: dict[str, Any] | None, dialect: Dialect
    ) -> PassengerFeatures | None:
        if value is None:
            return None
        return PassengerFeatures(
            total_tickets=value.get("total_tickets", 0),
            refund_cnt=value.get("refund_cnt", 0),
            refund_share=value.get("refund_share", 0.0),
            night_tickets=value.get("night_tickets", 0),
            night_share=value.get("night_share", 0.0),
            max_tickets_month=value.get("max_tickets_month", 0),
            max_tickets_same_depday=value.get("max_tickets_same_depday", 0),
            refund_close_ratio=value.get("refund_close_ratio", 0.0),
            tickets_per_train_peak=value.get("tickets_per_train_peak", 0.0),
            fio_fake_score_max=value.get("fio_fake_score_max", 0.0),
        )


class PassengerScoreType(TypeDecorator):
    """Custom type for serializing/deserializing PassengerScore to/from JSON"""
    impl = JSON
    cache_ok = True

    def process_bind_param(
        self, value: PassengerScore | None, dialect: Dialect
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        return {
            "rule_score": value.rule_score,
            "ml_score": value.ml_score,
            "final_score": value.final_score,
            "risk_band": value.risk_band.value,
            "top_reasons": value.top_reasons,
            "seat_blocking_flag": value.seat_blocking_flag,
            "scored_at": value.scored_at.isoformat() if value.scored_at else None,
        }

    def process_result_value(
        self, value: dict[str, Any] | None, dialect: Dialect
    ) -> PassengerScore | None:
        if value is None:
            return None
        scored_at = None
        if value.get("scored_at"):
            scored_at = datetime.fromisoformat(value["scored_at"])

        return PassengerScore(
            rule_score=value.get("rule_score", 0.0),
            ml_score=value.get("ml_score", 0.0),
            final_score=value.get("final_score", 0.0),
            risk_band=RiskBand(value.get("risk_band", "low")),
            top_reasons=value.get("top_reasons", []),
            seat_blocking_flag=value.get("seat_blocking_flag", False),
            scored_at=scored_at,
        )
