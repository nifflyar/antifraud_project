"""
Materialized statistics - pre-compute aggregates in database.
Instead of SELECT COUNT(*) WHERE risk_band='critical' every request,
we have a pre-calculated row that updates every 1 minute in background.
"""

from sqlalchemy import Column, String, Integer, TIMESTAMP, func
from datetime import datetime, UTC
from app.infrastructure.db.models.base import BaseORMModel


class PassengerStatisticsModel(BaseORMModel):
    """
    Materialized view of passenger statistics.
    Updated every 1 minute by background job.
    Query returns instant with zero latency.
    """
    __tablename__ = "passenger_statistics"

    id: str = Column(String(50), primary_key=True, default="current")
    total_passengers: int = Column(Integer, default=0)
    critical_risk_count: int = Column(Integer, default=0)
    high_risk_count: int = Column(Integer, default=0)
    medium_risk_count: int = Column(Integer, default=0)
    low_risk_count: int = Column(Integer, default=0)
    updated_at: datetime = Column(TIMESTAMP(timezone=True), server_default=func.now())


class TransactionStatisticsModel(BaseORMModel):
    """
    Materialized statistics for transactions.
    One-row table updated every 1 minute.
    """
    __tablename__ = "transaction_statistics"

    id: str = Column(String(50), primary_key=True, default="current")
    total_operations: int = Column(Integer, default=0)
    suspicious_operations: int = Column(Integer, default=0)
    refund_operations: int = Column(Integer, default=0)
    updated_at: datetime = Column(TIMESTAMP(timezone=True), server_default=func.now())


# Background job code
import logging
import asyncio
from sqlalchemy import select, update
from app.infrastructure.db.models.passenger_scores import PassengerScoreModel
from app.infrastructure.db.models.transaction import TransactionModel
from app.domain.transaction.vo import OperationType

logger = logging.getLogger(__name__)


async def update_materialized_statistics(session):
    """
    Run every 1 minute to update materialized statistics.
    This replaces 5 COUNT queries with 1 SELECT from single row.
    """
    try:
        # Update passenger statistics
        stmt = select(
            func.count().label("total"),
            func.sum((PassengerScoreModel.risk_band == "critical").cast(Integer)).label("critical"),
            func.sum((PassengerScoreModel.risk_band == "high").cast(Integer)).label("high"),
            func.sum((PassengerScoreModel.risk_band == "medium").cast(Integer)).label("medium"),
            func.sum((PassengerScoreModel.risk_band == "low").cast(Integer)).label("low"),
        )
        result = await session.execute(stmt)
        row = result.first()

        if row:
            await session.execute(
                update(PassengerStatisticsModel)
                .where(PassengerStatisticsModel.id == "current")
                .values(
                    total_passengers=row[0] or 0,
                    critical_risk_count=row[1] or 0,
                    high_risk_count=row[2] or 0,
                    medium_risk_count=row[3] or 0,
                    low_risk_count=row[4] or 0,
                    updated_at=datetime.now(UTC),
                )
            )

        logger.info("✅ Materialized statistics updated")
        await session.commit()
    except Exception as e:
        logger.error(f"❌ Failed to update materialized statistics: {e}")
        await session.rollback()
