from app.domain.passenger.entity import Passenger, PassengerFeatures, PassengerScore
from app.domain.passenger.vo import PassengerId, RiskBand
from app.infrastructure.db.models.passenger import PassengerModel
from app.infrastructure.db.models.passenger_features import PassengerFeaturesModel
from app.infrastructure.db.models.passenger_scores import PassengerScoreModel


def _normalize_top_reasons(raw_reasons: list | None) -> list[str]:
    reasons: list[str] = []
    for reason in raw_reasons or []:
        if isinstance(reason, str):
            reasons.append(reason)
            continue
        if isinstance(reason, dict):
            text = reason.get("text") or reason.get("code")
            if text:
                reasons.append(str(text))
            continue
        if reason is not None:
            reasons.append(str(reason))
    return reasons


class PassengerMapper:
    @staticmethod
    def to_domain(model: PassengerModel) -> Passenger:
        return Passenger(
            id=model.id,
            fio_clean=model.fio_clean,
            fake_fio_score=model.fake_fio_score,
            first_seen_at=model.first_seen_at,
            last_seen_at=model.last_seen_at,
            features=None,
            score=None,
        )

    @staticmethod
    def to_model(passenger: Passenger) -> PassengerModel:
        return PassengerModel(
            id=passenger.id,
            fio_clean=passenger.fio_clean,
            fake_fio_score=passenger.fake_fio_score,
            first_seen_at=passenger.first_seen_at,
            last_seen_at=passenger.last_seen_at,
        )


class PassengerFeaturesMapper:
    @staticmethod
    def to_domain(model: PassengerFeaturesModel) -> PassengerFeatures:
        return PassengerFeatures(
            total_tickets=model.total_tickets,
            refund_cnt=model.refund_cnt,
            refund_share=model.refund_share,
            night_tickets=model.night_tickets,
            night_share=model.night_share,
            max_tickets_month=model.max_tickets_month,
            max_tickets_same_depday=model.max_tickets_same_depday,
            refund_close_ratio=model.refund_close_ratio,
            tickets_per_train_peak=model.tickets_per_train_peak,
            fio_fake_score_max=model.fio_fake_score_max,
            late_refunds=model.late_refunds,
            late_refund_share=model.late_refund_share,
            very_late_refunds=model.very_late_refunds,
            very_late_refund_share=model.very_late_refund_share,
            quick_refunds=model.quick_refunds,
            quick_refund_share=model.quick_refund_share,
            activity_days=model.activity_days,
            suspicious_refund_pattern_cnt=model.suspicious_refund_pattern_cnt,
            refund_amount_diversity=model.refund_amount_diversity,
            seat_blocking_flag=model.seat_blocking_flag,
        )

    @staticmethod
    def to_model(
        passenger_id: PassengerId, features: PassengerFeatures
    ) -> PassengerFeaturesModel:
        return PassengerFeaturesModel(
            passenger_id=passenger_id,
            total_tickets=features.total_tickets,
            refund_cnt=features.refund_cnt,
            refund_share=features.refund_share,
            night_tickets=features.night_tickets,
            night_share=features.night_share,
            max_tickets_month=features.max_tickets_month,
            max_tickets_same_depday=features.max_tickets_same_depday,
            refund_close_ratio=features.refund_close_ratio,
            tickets_per_train_peak=features.tickets_per_train_peak,
            fio_fake_score_max=features.fio_fake_score_max,
            late_refunds=features.late_refunds,
            late_refund_share=features.late_refund_share,
            very_late_refunds=features.very_late_refunds,
            very_late_refund_share=features.very_late_refund_share,
            quick_refunds=features.quick_refunds,
            quick_refund_share=features.quick_refund_share,
            activity_days=features.activity_days,
            suspicious_refund_pattern_cnt=features.suspicious_refund_pattern_cnt,
            refund_amount_diversity=features.refund_amount_diversity,
            seat_blocking_flag=features.has_seat_blocking_pattern(),
        )


class PassengerScoreMapper:
    @staticmethod
    def to_domain(model: PassengerScoreModel) -> PassengerScore:
        return PassengerScore(
            rule_score=model.rule_score,
            ml_score=model.ml_score,
            final_score=model.final_score,
            risk_band=RiskBand(model.risk_band),
            top_reasons=_normalize_top_reasons(model.top_reasons),
            seat_blocking_flag=model.seat_blocking_flag,
            is_manual=model.is_manual,
            scored_at=model.scored_at,
        )

    @staticmethod
    def to_model(
        passenger_id: PassengerId, score: PassengerScore
    ) -> PassengerScoreModel:
        return PassengerScoreModel(
            passenger_id=passenger_id,
            rule_score=score.rule_score,
            ml_score=score.ml_score,
            final_score=score.final_score,
            risk_band=score.risk_band.value,
            top_reasons=score.top_reasons,
            seat_blocking_flag=score.seat_blocking_flag,
            is_manual=score.is_manual,
            scored_at=score.scored_at,
        )
