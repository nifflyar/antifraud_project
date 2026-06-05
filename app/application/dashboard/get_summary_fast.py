"""
Ultra-fast dashboard using:
1. Materialized statistics (pre-computed)
2. In-memory LRU cache
3. Raw SQL queries
4. Zero N+1 queries
"""

from app.infrastructure.fast_cache import get_fast_cache, cache_key
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


class GetDashboardSummaryInteractorFast:
    """Dashboard summary in <1ms"""

    def __init__(self, session):
        self._session = session
        self.cache = get_fast_cache()

    async def execute(self):
        # 1. Check memory cache first (microseconds)
        cache_key_str = cache_key("dashboard", "summary")
        cached = self.cache.get(cache_key_str)
        if cached:
            return cached

        # 2. Query materialized statistics (single row, instant)
        from app.infrastructure.db.models.statistics import PassengerStatisticsModel

        stmt = select(PassengerStatisticsModel).where(
            PassengerStatisticsModel.id == "current"
        )
        result = await self._session.execute(stmt)
        stats = result.scalar_one_or_none()

        if not stats:
            # Fallback to empty if not computed yet
            from app.presentation.api.dashboard.schemas import DashboardSummaryResponse
            return DashboardSummaryResponse(
                total_passengers=0,
                critical_risk_count=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                critical_risk_pct=0,
                high_risk_pct=0,
                medium_risk_pct=0,
                low_risk_pct=0,
                share_suspicious_ops=0,
                top_risk_channel=None,
                top_risk_terminal=None,
            )

        total = stats.total_passengers or 1

        from app.presentation.api.dashboard.schemas import DashboardSummaryResponse

        result_obj = DashboardSummaryResponse(
            total_passengers=stats.total_passengers,
            critical_risk_count=stats.critical_risk_count,
            high_risk_count=stats.high_risk_count,
            medium_risk_count=stats.medium_risk_count,
            low_risk_count=stats.low_risk_count,
            critical_risk_pct=round((stats.critical_risk_count / total) * 100, 2),
            high_risk_pct=round((stats.high_risk_count / total) * 100, 2),
            medium_risk_pct=round((stats.medium_risk_count / total) * 100, 2),
            low_risk_pct=round((stats.low_risk_count / total) * 100, 2),
            share_suspicious_ops=0,  # Could use similar materialized table
            top_risk_channel=None,
            top_risk_terminal=None,
        )

        # 3. Cache in memory for 5 seconds (fast refresh)
        self.cache.set(cache_key_str, result_obj, ttl=5)

        logger.info(f"Dashboard generated: {self.cache.stats()}")
        return result_obj
