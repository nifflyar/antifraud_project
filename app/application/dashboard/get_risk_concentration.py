from app.domain.risk.repository import IRiskConcentrationRepository
from app.domain.risk.vo import DimensionType
from app.domain.transaction.repository import ITransactionRepository

class GetRiskConcentrationInteractor:
    def __init__(
        self,
        risk_repo: IRiskConcentrationRepository,
        transaction_repo: ITransactionRepository,
    ):
        self._risk_repo = risk_repo
        self._tx_repo = transaction_repo

    async def execute(self, dimension_type: str, live: bool = False):
        try:
            dtype = DimensionType(dimension_type.lower())
        except ValueError:
            raise ValueError(f"Invalid dimension type: {dimension_type}. Supported: CHANNEL, AGGREGATOR, TERMINAL, CASHDESK")

        from app.presentation.api.dashboard.schemas import RiskConcentrationItem, RiskConcentrationResponse

        if not live:
            concentrations = await self._risk_repo.get_all_by_dimension(dtype)
            return RiskConcentrationResponse(
                dimension_type=dtype.value,
                items=[
                    RiskConcentrationItem(
                        dimension_value=c.dimension_value,
                        total_ops=c.total_ops,
                        highrisk_ops=c.highrisk_ops,
                        share_highrisk_ops=c.share_highrisk_ops,
                        lift_vs_base=c.lift_vs_base,
                    )
                    for c in concentrations
                ],
            )

        stats = await self._tx_repo.get_dimension_stats_by_passenger_score(dimension_column=dtype.value)
        total_ops = sum(row["total_count"] for row in stats)
        total_risky_ops = sum(row["suspicious_count"] for row in stats)
        base_share = total_risky_ops / total_ops if total_ops else 0.0

        items = [
            RiskConcentrationItem(
                dimension_value=str(row["value"]),
                total_ops=row["total_count"],
                highrisk_ops=row["suspicious_count"],
                share_highrisk_ops=(row["suspicious_count"] / row["total_count"]) if row["total_count"] else 0.0,
                lift_vs_base=((row["suspicious_count"] / row["total_count"]) / base_share) if row["total_count"] and base_share else 1.0,
            )
            for row in stats
        ]

        return RiskConcentrationResponse(dimension_type=dtype.value, items=items)
