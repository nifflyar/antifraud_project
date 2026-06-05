from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.domain.passenger.entity import PassengerFeatures
from app.domain.passenger.feature_repository import IPassengerFeatureRepository
from app.domain.passenger.vo import PassengerId
from app.infrastructure.db.mappers.passenger import PassengerFeaturesMapper
from app.infrastructure.db.models.passenger_features import PassengerFeaturesModel
from app.infrastructure.db.repos.base import BaseSQLAlchemyRepo


class PassengerFeatureRepositoryImpl(IPassengerFeatureRepository, BaseSQLAlchemyRepo):

    async def get_by_passenger_id(
        self, passenger_id: PassengerId
    ) -> PassengerFeatures | None:
        stmt = select(PassengerFeaturesModel).where(
            PassengerFeaturesModel.passenger_id == passenger_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return PassengerFeaturesMapper.to_domain(model) if model else None

    async def save(
        self, passenger_id: PassengerId, features: PassengerFeatures
    ) -> None:
        model = PassengerFeaturesMapper.to_model(passenger_id, features)
        await self._session.merge(model)
        await self._session.flush()

    async def bulk_upsert(
        self, items: list[tuple[PassengerId, PassengerFeatures]]
    ) -> None:
        """INSERT ... ON CONFLICT DO UPDATE — идемпотентная операция ETL."""
        if not items:
            return
        rows = [
            {
                "passenger_id": pid.value,
                "total_tickets": f.total_tickets,
                "refund_cnt": f.refund_cnt,
                "refund_share": f.refund_share,
                "night_tickets": f.night_tickets,
                "night_share": f.night_share,
                "max_tickets_month": f.max_tickets_month,
                "max_tickets_same_depday": f.max_tickets_same_depday,
                "refund_close_ratio": f.refund_close_ratio,
                "tickets_per_train_peak": f.tickets_per_train_peak,
                "fio_fake_score_max": f.fio_fake_score_max,
                "late_refunds": f.late_refunds,
                "late_refund_share": f.late_refund_share,
                "very_late_refunds": f.very_late_refunds,
                "very_late_refund_share": f.very_late_refund_share,
                "quick_refunds": f.quick_refunds,
                "quick_refund_share": f.quick_refund_share,
                "activity_days": f.activity_days,
                "suspicious_refund_pattern_cnt": f.suspicious_refund_pattern_cnt,
                "refund_amount_diversity": f.refund_amount_diversity,
                "seat_blocking_flag": f.has_seat_blocking_pattern(),
            }
            for pid, f in items
        ]
        stmt = insert(PassengerFeaturesModel).on_conflict_do_update(
            index_elements=["passenger_id"],
            set_={
                "total_tickets": insert(PassengerFeaturesModel).excluded.total_tickets,
                "refund_cnt": insert(PassengerFeaturesModel).excluded.refund_cnt,
                "refund_share": insert(PassengerFeaturesModel).excluded.refund_share,
                "night_tickets": insert(PassengerFeaturesModel).excluded.night_tickets,
                "night_share": insert(PassengerFeaturesModel).excluded.night_share,
                "max_tickets_month": insert(PassengerFeaturesModel).excluded.max_tickets_month,
                "max_tickets_same_depday": insert(PassengerFeaturesModel).excluded.max_tickets_same_depday,
                "refund_close_ratio": insert(PassengerFeaturesModel).excluded.refund_close_ratio,
                "tickets_per_train_peak": insert(PassengerFeaturesModel).excluded.tickets_per_train_peak,
                "fio_fake_score_max": insert(PassengerFeaturesModel).excluded.fio_fake_score_max,
                "late_refunds": insert(PassengerFeaturesModel).excluded.late_refunds,
                "late_refund_share": insert(PassengerFeaturesModel).excluded.late_refund_share,
                "very_late_refunds": insert(PassengerFeaturesModel).excluded.very_late_refunds,
                "very_late_refund_share": insert(PassengerFeaturesModel).excluded.very_late_refund_share,
                "quick_refunds": insert(PassengerFeaturesModel).excluded.quick_refunds,
                "quick_refund_share": insert(PassengerFeaturesModel).excluded.quick_refund_share,
                "activity_days": insert(PassengerFeaturesModel).excluded.activity_days,
                "suspicious_refund_pattern_cnt": insert(PassengerFeaturesModel).excluded.suspicious_refund_pattern_cnt,
                "refund_amount_diversity": insert(PassengerFeaturesModel).excluded.refund_amount_diversity,
                "seat_blocking_flag": insert(PassengerFeaturesModel).excluded.seat_blocking_flag,
            },
        )
        await self._session.execute(stmt, rows)

    async def delete_by_passenger_id(self, passenger_id: PassengerId) -> None:
        from sqlalchemy import delete
        stmt = delete(PassengerFeaturesModel).where(
            PassengerFeaturesModel.passenger_id == passenger_id
        )
        await self._session.execute(stmt)
