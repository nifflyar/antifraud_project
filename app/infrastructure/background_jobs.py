"""
Background scheduler for materialized statistics updates.
Updates every 60 seconds so dashboard is always fresh but instant.
"""

import asyncio
import logging
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.dialects.postgresql import insert
from app.infrastructure.db.models.passenger_scores import PassengerScoreModel
from app.infrastructure.db.models.statistics import PassengerStatisticsModel

logger = logging.getLogger(__name__)


async def refresh_materialized_stats(session_factory) -> None:
    """
    Runs every 60 seconds to refresh materialized statistics.
    This replaces expensive COUNT queries with instant lookups.
    """
    while True:
        try:
            async with session_factory() as session:
                # Count by risk band in single query
                stmt = select(
                    PassengerScoreModel.risk_band,
                    func.count().label("cnt")
                ).group_by(PassengerScoreModel.risk_band)

                result = await session.execute(stmt)
                counts = {row[0]: row[1] for row in result.all()}

                total = sum(counts.values())
                critical = counts.get("critical", 0)
                high = counts.get("high", 0)
                medium = counts.get("medium", 0)
                low = counts.get("low", 0)

                # Upsert (insert or update) the stats row
                stmt = insert(PassengerStatisticsModel).values(
                    id="current",
                    total_passengers=total,
                    critical_risk_count=critical,
                    high_risk_count=high,
                    medium_risk_count=medium,
                    low_risk_count=low,
                    updated_at=datetime.now(UTC)
                )

                # PostgreSQL upsert syntax
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_=dict(
                        total_passengers=total,
                        critical_risk_count=critical,
                        high_risk_count=high,
                        medium_risk_count=medium,
                        low_risk_count=low,
                        updated_at=datetime.now(UTC)
                    )
                )

                await session.execute(stmt)
                await session.commit()

                logger.info(f"✅ Stats refreshed: total={total}, critical={critical}, high={high}, medium={medium}, low={low}")

        except Exception as e:
            logger.error(f"❌ Error refreshing stats: {e}", exc_info=True)

        # Sleep for 60 seconds
        await asyncio.sleep(60)


def start_stats_refresh(session_factory) -> asyncio.Task:
    """Start background stats refresh task"""
    task = asyncio.create_task(refresh_materialized_stats(session_factory))
    logger.info("✅ Started materialized statistics refresh task")
    return task
