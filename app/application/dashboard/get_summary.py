from app.domain.passenger.repository import IPassengerRepository
from app.domain.passenger.vo import RiskBand
from app.domain.transaction.repository import ITransactionRepository
from app.domain.risk.repository import IRiskConcentrationRepository
from app.domain.risk.vo import DimensionType
from app.infrastructure.cache import get_cache, CacheManager

class GetDashboardSummaryInteractor:
    def __init__(
        self,
        passenger_repo: IPassengerRepository,
        transaction_repo: ITransactionRepository,
        risk_repo: IRiskConcentrationRepository,
    ):
        self._passenger_repo = passenger_repo
        self._transaction_repo = transaction_repo
        self._risk_repo = risk_repo

    async def execute(self):
        # Check cache first (5 min TTL for dashboard)
        cache = await get_cache()
        cache_key = CacheManager.make_key("dashboard", "summary")
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # 1. Get all passenger risk counts in one query (instead of 5 separate queries)
        risk_counts = await self._passenger_repo.count_all_risk_bands()
        total_passengers = sum(risk_counts.values())

        critical_risk_count = risk_counts.get("critical", 0)
        high_risk_count = risk_counts.get("high", 0)
        medium_risk_count = risk_counts.get("medium", 0)
        low_risk_count = risk_counts.get("low", 0)

        # Calculate percentages
        if total_passengers > 0:
            critical_risk_pct = round((critical_risk_count / total_passengers) * 100, 2)
            high_risk_pct = round((high_risk_count / total_passengers) * 100, 2)
            medium_risk_pct = round((medium_risk_count / total_passengers) * 100, 2)
            low_risk_pct = round((low_risk_count / total_passengers) * 100, 2)
        else:
            critical_risk_pct = high_risk_pct = medium_risk_pct = low_risk_pct = 0.0

        # 2. Транзакции
        total_ops = await self._transaction_repo.count_all()
        suspicious_ops = await self._transaction_repo.count_suspicious()

        share_suspicious = (suspicious_ops / total_ops * 100) if total_ops > 0 else 0.0

        # 3. Топ риски
        top_channel = await self._risk_repo.get_top_dimension("CHANNEL")
        top_terminal = await self._risk_repo.get_top_dimension("TERMINAL")

        from app.presentation.api.dashboard.schemas import DashboardSummaryResponse
        result = DashboardSummaryResponse(
            total_passengers=total_passengers,
            critical_risk_count=critical_risk_count,
            high_risk_count=high_risk_count,
            medium_risk_count=medium_risk_count,
            low_risk_count=low_risk_count,
            critical_risk_pct=critical_risk_pct,
            high_risk_pct=high_risk_pct,
            medium_risk_pct=medium_risk_pct,
            low_risk_pct=low_risk_pct,
            share_suspicious_ops=round(share_suspicious, 2),
            top_risk_channel=top_channel.dimension_value if top_channel else None,
            top_risk_terminal=top_terminal.dimension_value if top_terminal else None,
        )

        # Cache the result
        await cache.set(cache_key, result.dict(), ttl=300)
        return result
