from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.domain.passenger.entity import PassengerScore
from app.domain.passenger.score_repository import IPassengerScoreRepository
from app.domain.passenger.vo import PassengerId, RiskBand
from app.infrastructure.db.mappers.passenger import PassengerScoreMapper
from app.infrastructure.db.models.passenger_scores import PassengerScoreModel
from app.infrastructure.db.repos.base import BaseSQLAlchemyRepo


class PassengerScoreRepositoryImpl(IPassengerScoreRepository, BaseSQLAlchemyRepo):

    async def get_by_passenger_id(
        self, passenger_id: PassengerId
    ) -> PassengerScore | None:
        stmt = select(PassengerScoreModel).where(
            PassengerScoreModel.passenger_id == passenger_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return PassengerScoreMapper.to_domain(model) if model else None

    async def save(
        self, passenger_id: PassengerId, score: PassengerScore
    ) -> None:
        model = PassengerScoreMapper.to_model(passenger_id, score)
        await self._session.merge(model)
        await self._session.flush()

    async def bulk_upsert(
        self, items: list[tuple[PassengerId, PassengerScore]]
    ) -> None:
        """INSERT ... ON CONFLICT DO UPDATE — вызывается после ML-скоринга."""
        if not items:
            return
        rows = [
            {
                "passenger_id": pid.value,
                "rule_score": s.rule_score,
                "ml_score": s.ml_score,
                "final_score": s.final_score,
                "risk_band": s.risk_band.value,
                "top_reasons": s.top_reasons,
                "seat_blocking_flag": s.seat_blocking_flag,
                "is_manual": s.is_manual,
                "scored_at": s.scored_at,
            }
            for pid, s in items
        ]
        stmt = insert(PassengerScoreModel).on_conflict_do_update(
            index_elements=["passenger_id"],
            set_={
                "rule_score": insert(PassengerScoreModel).excluded.rule_score,
                "ml_score": insert(PassengerScoreModel).excluded.ml_score,
                "final_score": insert(PassengerScoreModel).excluded.final_score,
                "risk_band": insert(PassengerScoreModel).excluded.risk_band,
                "top_reasons": insert(PassengerScoreModel).excluded.top_reasons,
                "seat_blocking_flag": insert(PassengerScoreModel).excluded.seat_blocking_flag,
                "scored_at": insert(PassengerScoreModel).excluded.scored_at,
            },
            # Только если риск не был установлен вручную
            where=(PassengerScoreModel.is_manual == False),
        )
        await self._session.execute(stmt, rows)

    async def count_by_risk_band(self, risk_band: RiskBand) -> int:
        stmt = (
            select(func.count(PassengerScoreModel.passenger_id))
            .where(PassengerScoreModel.risk_band == risk_band.value)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def delete_by_passenger_id(self, passenger_id: PassengerId) -> None:
        from sqlalchemy import delete
        stmt = delete(PassengerScoreModel).where(
            PassengerScoreModel.passenger_id == passenger_id
        )
        await self._session.execute(stmt)
