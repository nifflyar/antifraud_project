from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.domain.risk.entity import RiskConcentration
from app.domain.risk.repository import IRiskConcentrationRepository
from app.domain.risk.vo import DimensionType, RiskConcentrationId
from app.infrastructure.db.models.risk_concentration import RiskConcentrationModel
from app.infrastructure.db.repos.base import BaseSQLAlchemyRepo


class RiskConcentrationRepositoryImpl(IRiskConcentrationRepository, BaseSQLAlchemyRepo):

    async def get_all_by_dimension(
        self, dimension_type: DimensionType
    ) -> list[RiskConcentration]:
        stmt = (
            select(RiskConcentrationModel)
            .where(RiskConcentrationModel.dimension_type == dimension_type.value)
            .order_by(RiskConcentrationModel.lift_vs_base.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_top_dimension(
        self, dimension_type: str, top_n: int = 1
    ) -> RiskConcentration | None:
        stmt = (
            select(RiskConcentrationModel)
            .where(RiskConcentrationModel.dimension_type == dimension_type)
            .order_by(RiskConcentrationModel.lift_vs_base.desc())
            .limit(top_n)
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_domain(model) if model else None

    async def save_batch(self, items: list[RiskConcentration]) -> None:
        """INSERT ... ON CONFLICT DO UPDATE по (dimension_type, dimension_value)."""
        if not items:
            return
        rows = [
            {
                "id": item.id.value,
                "dimension_type": item.dimension_type.value,
                "dimension_value": item.dimension_value,
                "total_ops": item.total_ops,
                "highrisk_ops": item.highrisk_ops,
                "share_highrisk_ops": item.share_highrisk_ops,
                "lift_vs_base": item.lift_vs_base,
                "calculated_at": item.calculated_at,
            }
            for item in items
        ]
        stmt = insert(RiskConcentrationModel).on_conflict_do_update(
            index_elements=["id"],
            set_={
                "total_ops": insert(RiskConcentrationModel).excluded.total_ops,
                "highrisk_ops": insert(RiskConcentrationModel).excluded.highrisk_ops,
                "share_highrisk_ops": insert(RiskConcentrationModel).excluded.share_highrisk_ops,
                "lift_vs_base": insert(RiskConcentrationModel).excluded.lift_vs_base,
                "calculated_at": insert(RiskConcentrationModel).excluded.calculated_at,
            },
        )
        await self._session.execute(stmt, rows)

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(model: RiskConcentrationModel) -> RiskConcentration:
        return RiskConcentration(
            id=model.id,
            dimension_type=DimensionType(model.dimension_type),
            dimension_value=model.dimension_value,
            total_ops=model.total_ops,
            highrisk_ops=model.highrisk_ops,
            share_highrisk_ops=model.share_highrisk_ops,
            lift_vs_base=model.lift_vs_base,
            calculated_at=model.calculated_at,
        )
