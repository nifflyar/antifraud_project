from datetime import datetime, timedelta
from typing import Optional
from app.domain.passenger.repository import IPassengerRepository
from app.domain.passenger.vo import RiskBand
from app.domain.transaction.repository import ITransactionRepository

class GetRiskStatsInteractor:
    """Get risk statistics for a specific period (day/week/month)."""

    def __init__(
        self,
        passenger_repo: IPassengerRepository,
        transaction_repo: ITransactionRepository,
    ):
        self._passenger_repo = passenger_repo
        self._transaction_repo = transaction_repo

    async def execute(
        self,
        period: str = "all",  # all, today, week, month
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ):
        """
        Get risk stats for specified period.

        Args:
            period: 'all', 'today', 'week', 'month'
            date_from: Custom start date
            date_to: Custom end date
        """
        # Determine date range
        now = datetime.utcnow()

        if date_from and date_to:
            start_date = date_from
            end_date = date_to
            period_label = f"from {date_from.date()} to {date_to.date()}"
        elif period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            period_label = "Today"
        elif period == "week":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            period_label = "This Week"
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            period_label = "This Month"
        else:  # all
            start_date = None
            end_date = None
            period_label = "All Time"

        # Query transactions in period
        if start_date and end_date:
            total_ops = await self._transaction_repo.count_by_date_range(start_date, end_date)
            critical_ops = await self._transaction_repo.count_critical_by_date_range(start_date, end_date)
            high_ops = await self._transaction_repo.count_high_by_date_range(start_date, end_date)
            medium_ops = await self._transaction_repo.count_medium_by_date_range(start_date, end_date)
            low_ops = await self._transaction_repo.count_low_by_date_range(start_date, end_date)
        else:
            total_ops = await self._transaction_repo.count_all()
            critical_ops = await self._transaction_repo.count_critical()
            high_ops = await self._transaction_repo.count_high()
            medium_ops = await self._transaction_repo.count_medium()
            low_ops = await self._transaction_repo.count_low()

        # Query passengers in period
        if start_date and end_date:
            total_passengers = await self._passenger_repo.count_by_date_range(start_date, end_date)
        else:
            total_passengers = await self._passenger_repo.count()

        # Calculate percentages
        if total_ops > 0:
            critical_pct = round((critical_ops / total_ops) * 100, 2)
            high_pct = round((high_ops / total_ops) * 100, 2)
            medium_pct = round((medium_ops / total_ops) * 100, 2)
            low_pct = round((low_ops / total_ops) * 100, 2)
        else:
            critical_pct = high_pct = medium_pct = low_pct = 0.0

        from app.presentation.api.dashboard.schemas import RiskStatsResponse
        return RiskStatsResponse(
            period=period_label,
            date_from=start_date,
            date_to=end_date,
            total_passengers=total_passengers,
            total_ops=total_ops,
            critical_ops=critical_ops,
            high_ops=high_ops,
            medium_ops=medium_ops,
            low_ops=low_ops,
            critical_pct=critical_pct,
            high_pct=high_pct,
            medium_pct=medium_pct,
            low_pct=low_pct,
        )
