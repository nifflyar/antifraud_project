from datetime import datetime
from app.domain.transaction.repository import ITransactionRepository

class GetRiskTrendInteractor:
    def __init__(self, transaction_repo: ITransactionRepository):
        self._transaction_repo = transaction_repo

    async def execute(self, date_from: datetime | None = None, date_to: datetime | None = None):
        trend_data = await self._transaction_repo.get_risk_trend(date_from, date_to)
        
        from app.presentation.api.dashboard.schemas import RiskTrendItem, RiskTrendResponse
        
        items = []
        for row in trend_data:
            share = (row["suspicious_count"] / row["total_count"] * 100) if row["total_count"] > 0 else 0.0
            items.append(RiskTrendItem(
                date=row["date"],
                total_ops=row["total_count"],
                highrisk_ops=row["suspicious_count"],
                critical_ops=row.get("critical_count", 0),
                share=round(share, 2)
            ))
            
        return RiskTrendResponse(items=items)
