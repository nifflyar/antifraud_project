from collections import defaultdict
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert

from app.domain.passenger.vo import PassengerId, RiskBand
from app.domain.transaction.entity import Transaction
from app.domain.transaction.repository import ITransactionRepository
from app.domain.transaction.vo import OperationType, TransactionId
from app.domain.upload.vo import UploadId
from app.infrastructure.db.mappers.transaction import TransactionMapper
from app.infrastructure.db.models.passenger import PassengerModel
from app.infrastructure.db.models.passenger_features import PassengerFeaturesModel
from app.infrastructure.db.models.passenger_scores import PassengerScoreModel
from app.infrastructure.db.models.transaction import TransactionModel
from app.infrastructure.db.repos.base import BaseSQLAlchemyRepo
from app.infrastructure.di.caching import cache_result

_SUSPICIOUS_BANDS = (RiskBand.high.value, RiskBand.critical.value)
_TRANSACTION_COPY_COLUMNS = (
    "id",
    "upload_id",
    "source",
    "op_type",
    "op_datetime",
    "dep_datetime",
    "train_no",
    "channel",
    "aggregator",
    "terminal",
    "cashdesk",
    "point_of_sale",
    "amount",
    "fee",
    "fio",
    "iin",
    "doc_no",
    "phone",
    "gender",
    "ticket_no",
    "tariff_type",
    "service_class",
    "branch",
    "sale_user",
    "carrier",
    "settlement_type",
    "order_no",
    "dep_station",
    "arr_station",
    "route",
    "passenger_id",
)

_TRANSACTION_STRING_LIMITS = {
    "source": 50,
    "train_no": 50,
    "channel": 100,
    "aggregator": 100,
    "terminal": 100,
    "cashdesk": 100,
    "point_of_sale": 100,
    "fio": 255,
    "iin": 20,
    "doc_no": 50,
    "phone": 50,
    "gender": 20,
    "ticket_no": 50,
    "tariff_type": 100,
    "service_class": 100,
    "branch": 150,
    "sale_user": 150,
    "carrier": 150,
    "settlement_type": 100,
    "order_no": 50,
    "dep_station": 255,
    "arr_station": 255,
    "route": 512,
}


def _clip_text(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    return value[:max_len]


def _suspicious_cache_key(**kwargs) -> str:
    parts = []
    for key in (
        "train_no",
        "cashdesk",
        "terminal",
        "channel",
        "aggregator",
        "point_of_sale",
        "op_type",
        "search",
        "date_from",
        "date_to",
        "limit",
        "offset",
        "sort_by",
        "sort_order",
    ):
        value = kwargs.get(key)
        parts.append(f"{key}={value.isoformat() if hasattr(value, 'isoformat') else value}")
    return "suspicious:" + "|".join(parts)


def _dimension_stats_cache_key(**kwargs) -> str:
    return f"dimension_stats:{kwargs.get('dimension_column')}"


class TransactionRepositoryImpl(ITransactionRepository, BaseSQLAlchemyRepo):

    async def get_by_id(self, transaction_id: TransactionId) -> Transaction | None:
        stmt = select(TransactionModel).where(TransactionModel.id == transaction_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return TransactionMapper.to_domain(model) if model else None

    async def get_all_by_upload_id(
        self, upload_id: UploadId, limit: int = 500, offset: int = 0
    ) -> list[Transaction]:
        stmt = (
            select(TransactionModel)
            .where(TransactionModel.upload_id == upload_id)
            .order_by(TransactionModel.op_datetime.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [TransactionMapper.to_domain(m) for m in result.scalars().all()]

    async def get_by_passenger_id(
        self, passenger_id: PassengerId, limit: int = 100, offset: int = 0
    ) -> list[Transaction]:
        stmt = (
            select(TransactionModel)
            .where(TransactionModel.passenger_id == passenger_id)
            .order_by(TransactionModel.op_datetime.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [TransactionMapper.to_domain(m) for m in result.scalars().all()]

    async def count_by_passenger_id(self, passenger_id: PassengerId) -> int:
        stmt = select(func.count(TransactionModel.id)).where(
            TransactionModel.passenger_id == passenger_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    @cache_result(ttl=30, cache_key_fn=_suspicious_cache_key)
    async def get_suspicious(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "risk_score",
        sort_order: str = "desc",
    ) -> list[tuple[Transaction, RiskBand, int, list[str]]]:
        max_rows_to_scan = 10000
        scored = await self._get_scored_operations(
            train_no=train_no,
            cashdesk=cashdesk,
            terminal=terminal,
            channel=channel,
            aggregator=aggregator,
            point_of_sale=point_of_sale,
            date_from=date_from,
            date_to=date_to,
            limit=max_rows_to_scan,
        )
        suspicious = [item for item in scored if item["operation_score"] >= 40]
        suspicious = self._sort_scored_operations(suspicious, sort_by, sort_order)
        page = suspicious[offset : offset + limit]
        return [
            (
                item["tx"],
                item["operation_band"],
                item["operation_score"],
                item["operation_reasons"],
            )
            for item in page
        ]

    async def get_operations(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        op_type: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> list[tuple[Transaction, RiskBand, int, list[str]]]:
        should_score_full_set = bool(terminal or cashdesk or point_of_sale or search or train_no)
        db_sortable = sort_by in {"date", "amount", "train_no", "passenger"}

        if should_score_full_set:
            scored = await self._get_scored_operations(
                train_no=train_no,
                cashdesk=cashdesk,
                terminal=terminal,
                channel=channel,
                aggregator=aggregator,
                point_of_sale=point_of_sale,
                op_type=op_type,
                search=search,
                date_from=date_from,
                date_to=date_to,
            )
            sorted_items = self._sort_scored_operations(scored, sort_by, sort_order)
            page = sorted_items[offset : offset + limit]
        elif db_sortable:
            page = await self._get_scored_operations_page_scan(
                train_no=train_no,
                cashdesk=cashdesk,
                terminal=terminal,
                channel=channel,
                aggregator=aggregator,
                point_of_sale=point_of_sale,
                op_type=op_type,
                search=search,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset,
                db_sort_by=sort_by,
                db_sort_order=sort_order,
            )
        else:
            max_rows_to_scan = min(max(offset + limit, 1000), 50000)
            scored = await self._get_scored_operations(
                train_no=train_no,
                cashdesk=cashdesk,
                terminal=terminal,
                channel=channel,
                aggregator=aggregator,
                point_of_sale=point_of_sale,
                op_type=op_type,
                search=search,
                date_from=date_from,
                date_to=date_to,
                limit=max_rows_to_scan,
            )
            sorted_items = self._sort_scored_operations(scored, sort_by, sort_order)
            page = sorted_items[offset : offset + limit]
        return [
            (
                item["tx"],
                item["operation_band"],
                item["operation_score"],
                item["operation_reasons"],
            )
            for item in page
        ]

    async def count_suspicious(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        max_rows_to_scan = 10000
        scored = await self._get_scored_operations(
            train_no=train_no,
            cashdesk=cashdesk,
            terminal=terminal,
            channel=channel,
            aggregator=aggregator,
            point_of_sale=point_of_sale,
            date_from=date_from,
            date_to=date_to,
            limit=max_rows_to_scan,
        )
        return sum(1 for item in scored if item["operation_score"] >= 40)

    async def count_scored_suspicious(self) -> int:
        """Fast approximate risk count based on saved passenger scores."""
        stmt = (
            select(func.count(TransactionModel.id))
            .join(
                PassengerScoreModel,
                TransactionModel.passenger_id == PassengerScoreModel.passenger_id,
            )
            .where(
                PassengerScoreModel.risk_band.in_(
                    [RiskBand.medium.value, RiskBand.high.value, RiskBand.critical.value]
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def count_operations(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        op_type: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        stmt = select(func.count(TransactionModel.id))
        stmt = self._apply_filters(
            stmt,
            train_no=train_no,
            cashdesk=cashdesk,
            terminal=terminal,
            channel=channel,
            aggregator=aggregator,
            point_of_sale=point_of_sale,
            op_type=op_type,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def get_operation_risk_stats(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        op_type: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict[str, int]:
        band_expr = PassengerScoreModel.risk_band
        critical_expr = case((band_expr == RiskBand.critical.value, 1), else_=0)
        high_expr = case((band_expr == RiskBand.high.value, 1), else_=0)
        medium_expr = case((band_expr == RiskBand.medium.value, 1), else_=0)

        stmt = (
            select(
                func.count(TransactionModel.id).label("total"),
                func.coalesce(func.sum(critical_expr), 0).label("critical"),
                func.coalesce(func.sum(high_expr), 0).label("high"),
                func.coalesce(func.sum(medium_expr), 0).label("medium"),
            )
            .outerjoin(
                PassengerScoreModel,
                TransactionModel.passenger_id == PassengerScoreModel.passenger_id,
            )
        )
        stmt = self._apply_filters(
            stmt,
            train_no=train_no,
            cashdesk=cashdesk,
            terminal=terminal,
            channel=channel,
            aggregator=aggregator,
            point_of_sale=point_of_sale,
            op_type=op_type,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        row = (await self._session.execute(stmt)).one()
        critical = int(row.critical or 0)
        high = int(row.high or 0)
        medium = int(row.medium or 0)
        total = int(row.total or 0)
        suspicious = medium + high + critical
        stats = {
            "low": max(total - suspicious, 0),
            "medium": medium,
            "high": high,
            "critical": critical,
        }
        stats["suspicious"] = stats["medium"] + stats["high"] + stats["critical"]
        stats["high_critical"] = stats["high"] + stats["critical"]
        return stats

    async def count_all(self) -> int:
        stmt = select(func.count(TransactionModel.id))
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def count_by_date_range(self, date_from: datetime, date_to: datetime) -> int:
        stmt = (
            select(func.count(TransactionModel.id))
            .where(TransactionModel.op_datetime >= date_from)
            .where(TransactionModel.op_datetime <= date_to)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def count_critical(self) -> int:
        return await self._count_operation_band(RiskBand.critical)

    async def count_high(self) -> int:
        return await self._count_operation_band(RiskBand.high)

    async def count_medium(self) -> int:
        return await self._count_operation_band(RiskBand.medium)

    async def count_low(self) -> int:
        return await self._count_operation_band(RiskBand.low)

    async def count_critical_by_date_range(self, date_from: datetime, date_to: datetime) -> int:
        return await self._count_operation_band(RiskBand.critical, date_from, date_to)

    async def count_high_by_date_range(self, date_from: datetime, date_to: datetime) -> int:
        return await self._count_operation_band(RiskBand.high, date_from, date_to)

    async def count_medium_by_date_range(self, date_from: datetime, date_to: datetime) -> int:
        return await self._count_operation_band(RiskBand.medium, date_from, date_to)

    async def count_low_by_date_range(self, date_from: datetime, date_to: datetime) -> int:
        return await self._count_operation_band(RiskBand.low, date_from, date_to)

    async def create_batch(self, transactions: list[Transaction]) -> None:
        """Bulk insert transactions via PostgreSQL COPY into a temp staging table."""
        if not transactions:
            return

        from sqlalchemy import text

        temp_table = "tmp_transactions_bulk"
        column_list = ", ".join(_TRANSACTION_COPY_COLUMNS)
        await self._session.execute(
            text(f"""
                CREATE TEMP TABLE IF NOT EXISTS {temp_table}
                (LIKE transactions INCLUDING DEFAULTS)
                ON COMMIT DROP
            """)
        )
        await self._session.execute(text(f"TRUNCATE TABLE {temp_table}"))

        conn = await self._session.connection()
        raw_conn = await conn.get_raw_connection()
        driver_conn = raw_conn.driver_connection

        chunk_size = 50000
        for chunk_start in range(0, len(transactions), chunk_size):
            chunk = transactions[chunk_start : chunk_start + chunk_size]
            try:
                await driver_conn.copy_records_to_table(
                    temp_table,
                    records=[self._to_copy_record(tx) for tx in chunk],
                    columns=_TRANSACTION_COPY_COLUMNS,
                )
            except Exception as exc:
                raise ValueError(
                    f"Ошибка bulk-вставки транзакций "
                    f"(строки чанка {chunk_start + 1}-{chunk_start + len(chunk)}): {exc}"
                ) from exc
            await self._session.execute(
                text(f"""
                    INSERT INTO transactions ({column_list})
                    SELECT {column_list}
                    FROM {temp_table}
                    ON CONFLICT (id) DO NOTHING
                """)
            )
            await self._session.execute(text(f"TRUNCATE TABLE {temp_table}"))

    @staticmethod
    def _to_copy_record(tx: Transaction) -> tuple:
        return (
            tx.id.value,
            tx.upload_id.value,
            _clip_text(tx.source, _TRANSACTION_STRING_LIMITS["source"]),
            tx.op_type.value,
            tx.op_datetime,
            tx.dep_datetime,
            _clip_text(tx.train_no, _TRANSACTION_STRING_LIMITS["train_no"]),
            _clip_text(tx.channel, _TRANSACTION_STRING_LIMITS["channel"]),
            _clip_text(tx.aggregator, _TRANSACTION_STRING_LIMITS["aggregator"]),
            _clip_text(tx.terminal, _TRANSACTION_STRING_LIMITS["terminal"]),
            _clip_text(tx.cashdesk, _TRANSACTION_STRING_LIMITS["cashdesk"]),
            _clip_text(tx.point_of_sale, _TRANSACTION_STRING_LIMITS["point_of_sale"]),
            tx.amount,
            tx.fee,
            _clip_text(tx.fio, _TRANSACTION_STRING_LIMITS["fio"]),
            _clip_text(tx.iin, _TRANSACTION_STRING_LIMITS["iin"]),
            _clip_text(tx.doc_no, _TRANSACTION_STRING_LIMITS["doc_no"]),
            _clip_text(tx.phone, _TRANSACTION_STRING_LIMITS["phone"]),
            _clip_text(tx.gender, _TRANSACTION_STRING_LIMITS["gender"]),
            _clip_text(tx.ticket_no, _TRANSACTION_STRING_LIMITS["ticket_no"]),
            _clip_text(tx.tariff_type, _TRANSACTION_STRING_LIMITS["tariff_type"]),
            _clip_text(tx.service_class, _TRANSACTION_STRING_LIMITS["service_class"]),
            _clip_text(tx.branch, _TRANSACTION_STRING_LIMITS["branch"]),
            _clip_text(tx.sale_user, _TRANSACTION_STRING_LIMITS["sale_user"]),
            _clip_text(tx.carrier, _TRANSACTION_STRING_LIMITS["carrier"]),
            _clip_text(tx.settlement_type, _TRANSACTION_STRING_LIMITS["settlement_type"]),
            _clip_text(tx.order_no, _TRANSACTION_STRING_LIMITS["order_no"]),
            _clip_text(tx.dep_station, _TRANSACTION_STRING_LIMITS["dep_station"]),
            _clip_text(tx.arr_station, _TRANSACTION_STRING_LIMITS["arr_station"]),
            _clip_text(tx.route, _TRANSACTION_STRING_LIMITS["route"]),
            tx.passenger_id.value if tx.passenger_id else None,
        )

    async def get_risk_trend(
        self, date_from: datetime | None = None, date_to: datetime | None = None
    ) -> list[dict]:
        """Возвращает статистику по дням: дата, общее кол-во, подозрительные операции."""
        day_expr = func.date_trunc("day", TransactionModel.op_datetime)
        stmt = (
            select(
                day_expr.label("day"),
                func.count(TransactionModel.id).label("total_count"),
            )
            .group_by(day_expr)
            .order_by(day_expr)
        )

        if date_from:
            stmt = stmt.where(TransactionModel.op_datetime >= date_from)
        if date_to:
            stmt = stmt.where(TransactionModel.op_datetime <= date_to)

        result = await self._session.execute(stmt)
        totals = {row.day: row.total_count for row in result.all()}

        max_rows_to_scan = 50000
        scored = await self._get_scored_operations(date_from=date_from, date_to=date_to, limit=max_rows_to_scan)
        suspicious_by_day: dict[datetime, int] = defaultdict(int)
        critical_by_day: dict[datetime, int] = defaultdict(int)
        for item in scored:
            if item["operation_score"] >= 40 and item["tx"].op_datetime:
                day = item["tx"].op_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
                suspicious_by_day[day] += 1
                if item["operation_score"] >= 80:
                    critical_by_day[day] += 1

        return [
            {
                "date": day,
                "total_count": total_count,
                "suspicious_count": suspicious_by_day.get(day, 0),
                "critical_count": critical_by_day.get(day, 0),
            }
            for day, total_count in sorted(totals.items(), key=lambda item: item[0])
        ]

    async def get_dimension_stats(self, dimension_column: str) -> list[dict]:
        """Группирует транзакции по колонке (channel, terminal и т.д.)
        и считает кол-во всего / подозрительных."""
        col = getattr(TransactionModel, dimension_column, None)
        if col is None:
            raise ValueError(f"Invalid dimension column: {dimension_column}")

        stmt = (
            select(
                col.label("dim"),
                func.count(TransactionModel.id).label("total_count"),
            )
            .group_by(col)
            .order_by(func.count(TransactionModel.id).desc())
        )

        result = await self._session.execute(stmt)
        totals = {str(row.dim): row.total_count for row in result.all() if row.dim is not None}

        max_rows_to_scan = 50000
        scored = await self._get_scored_operations(limit=max_rows_to_scan)
        suspicious_counts: dict[str, int] = defaultdict(int)
        for item in scored:
            if item["operation_score"] < 40:
                continue
            value = getattr(item["tx"], dimension_column, None)
            if value is not None:
                suspicious_counts[str(value)] += 1

        return [
            {
                "value": value,
                "total_count": total_count,
                "suspicious_count": suspicious_counts.get(value, 0),
            }
            for value, total_count in sorted(
                totals.items(), key=lambda item: suspicious_counts.get(item[0], 0), reverse=True
            )
        ]

    @cache_result(ttl=300, cache_key_fn=_dimension_stats_cache_key)
    async def get_dimension_stats_by_passenger_score(self, dimension_column: str) -> list[dict]:
        """Fast concentration stats using persisted passenger final scores."""
        col = getattr(TransactionModel, dimension_column, None)
        if col is None:
            raise ValueError(f"Invalid dimension column: {dimension_column}")

        suspicious_expr = case(
            (
                PassengerScoreModel.risk_band.in_(
                    [RiskBand.medium.value, RiskBand.high.value, RiskBand.critical.value]
                ),
                1,
            ),
            else_=0,
        )
        stmt = (
            select(
                col.label("dim"),
                func.count(TransactionModel.id).label("total_count"),
                func.coalesce(func.sum(suspicious_expr), 0).label("suspicious_count"),
            )
            .outerjoin(
                PassengerScoreModel,
                TransactionModel.passenger_id == PassengerScoreModel.passenger_id,
            )
            .where(col.is_not(None))
            .group_by(col)
            .order_by(
                func.coalesce(func.sum(suspicious_expr), 0).desc(),
                func.count(TransactionModel.id).desc(),
            )
        )

        result = await self._session.execute(stmt)
        return [
            {
                "value": str(row.dim),
                "total_count": int(row.total_count or 0),
                "suspicious_count": int(row.suspicious_count or 0),
            }
            for row in result.all()
        ]

    @cache_result(ttl=300, cache_key_fn=_dimension_stats_cache_key)
    async def get_live_dimension_stats(self, dimension_column: str) -> list[dict]:
        """Exact dashboard stats: score each dimension bucket using the same context as its detail view."""
        if getattr(TransactionModel, dimension_column, None) is None:
            raise ValueError(f"Invalid dimension column: {dimension_column}")

        stmt = select(TransactionModel)
        result = await self._session.execute(stmt)
        transactions = [TransactionMapper.to_domain(model) for model in result.scalars().all()]
        rows = await self._build_operation_rows_with_context(transactions)

        rows_by_dimension: dict[str, list[dict]] = defaultdict(list)
        for item in rows:
            value = getattr(item["tx"], dimension_column, None)
            if value is not None:
                rows_by_dimension[str(value)].append(item)

        totals = {value: len(items) for value, items in rows_by_dimension.items()}
        suspicious_counts: dict[str, int] = defaultdict(int)
        for value, dimension_rows in rows_by_dimension.items():
            suspicious_counts[value] = sum(
                1
                for item in self._score_operation_rows(dimension_rows)
                if item["operation_score"] >= 40
            )

        return [
            {
                "value": value,
                "total_count": total_count,
                "suspicious_count": suspicious_counts.get(value, 0),
            }
            for value, total_count in sorted(
                totals.items(), key=lambda item: suspicious_counts.get(item[0], 0), reverse=True
            )
        ]

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _apply_filters(
        stmt,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        op_type: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ):
        if train_no:
            stmt = stmt.where(TransactionModel.train_no == train_no)
        if cashdesk:
            stmt = stmt.where(
                (TransactionModel.cashdesk == cashdesk)
                | (TransactionModel.point_of_sale == cashdesk)
            )
        if terminal:
            stmt = stmt.where(TransactionModel.terminal == terminal)
        if channel:
            stmt = stmt.where(TransactionModel.channel == channel)
        if aggregator:
            stmt = stmt.where(TransactionModel.aggregator == aggregator)
        if point_of_sale:
            stmt = stmt.where(TransactionModel.point_of_sale == point_of_sale)
        if op_type:
            stmt = stmt.where(TransactionModel.op_type == OperationType(op_type))
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                (TransactionModel.ticket_no.ilike(pattern))
                | (TransactionModel.order_no.ilike(pattern))
                | (TransactionModel.fio.ilike(pattern))
                | (TransactionModel.iin.ilike(pattern))
                | (TransactionModel.doc_no.ilike(pattern))
                | (TransactionModel.phone.ilike(pattern))
            )
        if date_from:
            stmt = stmt.where(TransactionModel.op_datetime >= date_from)
        if date_to:
            stmt = stmt.where(TransactionModel.op_datetime <= date_to)
        return stmt

    async def _count_operation_band(
        self,
        risk_band: RiskBand,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        scored = await self._get_scored_operations(date_from=date_from, date_to=date_to)
        return sum(1 for item in scored if item["operation_band"] == risk_band)

    async def _get_scored_operations(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        op_type: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int | None = None,
        offset: int = 0,
        db_sort_by: str | None = None,
        db_sort_order: str = "desc",
    ) -> list[dict]:
        if limit is None and db_sort_by is None:
            return await self._get_scored_operations_full_scan(
                train_no=train_no,
                cashdesk=cashdesk,
                terminal=terminal,
                channel=channel,
                aggregator=aggregator,
                point_of_sale=point_of_sale,
                op_type=op_type,
                search=search,
                date_from=date_from,
                date_to=date_to,
            )

        stmt = (
            select(
                TransactionModel,
                PassengerScoreModel.risk_band,
                PassengerScoreModel.final_score,
                PassengerScoreModel.top_reasons,
                PassengerFeaturesModel.fio_fake_score_max,
                PassengerFeaturesModel.suspicious_refund_pattern_cnt,
                PassengerFeaturesModel.refund_amount_diversity,
                PassengerFeaturesModel.seat_blocking_flag,
                PassengerModel.fio_clean,
            )
            .outerjoin(
                PassengerScoreModel,
                TransactionModel.passenger_id == PassengerScoreModel.passenger_id,
            )
            .outerjoin(
                PassengerFeaturesModel,
                TransactionModel.passenger_id == PassengerFeaturesModel.passenger_id,
            )
            .outerjoin(
                PassengerModel,
                TransactionModel.passenger_id == PassengerModel.id,
            )
        )
        stmt = self._apply_filters(
            stmt,
            train_no=train_no,
            cashdesk=cashdesk,
            terminal=terminal,
            channel=channel,
            aggregator=aggregator,
            point_of_sale=point_of_sale,
            op_type=op_type,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        if db_sort_by:
            stmt = self._apply_db_operation_sort(stmt, db_sort_by, db_sort_order)
        elif limit:
            stmt = self._apply_db_operation_sort(stmt, "date", "desc")
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        result = await self._session.execute(stmt)
        rows = []
        for row in result.all():
            rows.append(
                {
                    "tx": TransactionMapper.to_domain(row[0]),
                    "passenger_band": row[1],
                    "passenger_score": float(row[2] or 0),
                    "passenger_reasons": row[3] or [],
                    "fio_fake_score": float(row[4] or 0),
                    "pattern_cnt": int(row[5] or 0),
                    "amount_diversity": float(row[6] or 1.0),
                    "seat_blocking_flag": bool(row[7]),
                    "passenger_fio_clean": row[8],
                }
            )
        scored = self._score_operation_rows(rows)
        for item in scored:
            passenger_fio_clean = item.get("passenger_fio_clean")
            if passenger_fio_clean:
                item["tx"].fio = passenger_fio_clean
        return scored

    async def _get_scored_operations_full_scan(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        op_type: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict]:
        stmt = select(TransactionModel)
        stmt = self._apply_filters(
            stmt,
            train_no=train_no,
            cashdesk=cashdesk,
            terminal=terminal,
            channel=channel,
            aggregator=aggregator,
            point_of_sale=point_of_sale,
            op_type=op_type,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        result = await self._session.execute(stmt)
        transactions = [TransactionMapper.to_domain(model) for model in result.scalars().all()]
        return await self._score_transactions_with_context(transactions)

    async def _get_scored_operations_page_scan(
        self,
        train_no: str | None = None,
        cashdesk: str | None = None,
        terminal: str | None = None,
        channel: str | None = None,
        aggregator: str | None = None,
        point_of_sale: str | None = None,
        op_type: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
        db_sort_by: str = "date",
        db_sort_order: str = "desc",
    ) -> list[dict]:
        stmt = select(TransactionModel)
        stmt = self._apply_filters(
            stmt,
            train_no=train_no,
            cashdesk=cashdesk,
            terminal=terminal,
            channel=channel,
            aggregator=aggregator,
            point_of_sale=point_of_sale,
            op_type=op_type,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        stmt = self._apply_db_operation_sort(stmt, db_sort_by, db_sort_order)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        transactions = [TransactionMapper.to_domain(model) for model in result.scalars().all()]
        return await self._score_transactions_with_context(transactions)

    async def _score_transactions_with_context(self, transactions: list[Transaction]) -> list[dict]:
        rows = await self._build_operation_rows_with_context(transactions)
        scored = self._score_operation_rows(rows)
        for item in scored:
            passenger_fio_clean = item.get("passenger_fio_clean")
            if passenger_fio_clean:
                item["tx"].fio = passenger_fio_clean
        return scored

    async def _build_operation_rows_with_context(self, transactions: list[Transaction]) -> list[dict]:
        passenger_ids = sorted(
            {
                tx.passenger_id.value
                for tx in transactions
                if tx.passenger_id is not None
            }
        )
        score_map, feature_map, fio_map = await self._load_operation_context_maps(passenger_ids)

        rows: list[dict] = []
        for tx in transactions:
            pid = tx.passenger_id.value if tx.passenger_id else None
            score = score_map.get(pid)
            features = feature_map.get(pid)
            rows.append(
                {
                    "tx": tx,
                    "passenger_band": score["risk_band"] if score else None,
                    "passenger_score": score["final_score"] if score else 0.0,
                    "passenger_reasons": score["top_reasons"] if score else [],
                    "fio_fake_score": features["fio_fake_score"] if features else 0.0,
                    "pattern_cnt": features["pattern_cnt"] if features else 0,
                    "amount_diversity": features["amount_diversity"] if features else 1.0,
                    "seat_blocking_flag": features["seat_blocking_flag"] if features else False,
                    "passenger_fio_clean": fio_map.get(pid),
                }
            )

        return rows

    async def _load_operation_context_maps(
        self, passenger_ids: list[int]
    ) -> tuple[dict[int, dict], dict[int, dict], dict[int, str]]:
        if not passenger_ids:
            return {}, {}, {}

        score_map: dict[int, dict] = {}
        feature_map: dict[int, dict] = {}
        fio_map: dict[int, str] = {}
        chunk_size = 10000

        for start in range(0, len(passenger_ids), chunk_size):
            chunk = passenger_ids[start : start + chunk_size]

            score_stmt = select(
                PassengerScoreModel.passenger_id,
                PassengerScoreModel.risk_band,
                PassengerScoreModel.final_score,
                PassengerScoreModel.top_reasons,
            ).where(PassengerScoreModel.passenger_id.in_(chunk))
            score_result = await self._session.execute(score_stmt)
            for row in score_result.all():
                score_map[row[0].value] = {
                    "risk_band": row[1],
                    "final_score": float(row[2] or 0),
                    "top_reasons": row[3] or [],
                }

            feature_stmt = select(
                PassengerFeaturesModel.passenger_id,
                PassengerFeaturesModel.fio_fake_score_max,
                PassengerFeaturesModel.suspicious_refund_pattern_cnt,
                PassengerFeaturesModel.refund_amount_diversity,
                PassengerFeaturesModel.seat_blocking_flag,
            ).where(PassengerFeaturesModel.passenger_id.in_(chunk))
            feature_result = await self._session.execute(feature_stmt)
            for row in feature_result.all():
                feature_map[row[0].value] = {
                    "fio_fake_score": float(row[1] or 0),
                    "pattern_cnt": int(row[2] or 0),
                    "amount_diversity": float(row[3] or 1.0),
                    "seat_blocking_flag": bool(row[4]),
                }

            passenger_stmt = select(
                PassengerModel.id,
                PassengerModel.fio_clean,
            ).where(PassengerModel.id.in_(chunk))
            passenger_result = await self._session.execute(passenger_stmt)
            for row in passenger_result.all():
                fio_map[row[0].value] = row[1]

        return score_map, feature_map, fio_map

    @staticmethod
    def _apply_db_operation_sort(stmt, sort_by: str, sort_order: str):
        sort_key = (sort_by or "date").lower()
        descending = sort_order.lower() != "asc"

        if sort_key == "amount":
            order_exprs = [
                TransactionModel.amount,
                TransactionModel.op_datetime,
                TransactionModel.id,
            ]
        elif sort_key == "train_no":
            order_exprs = [
                func.coalesce(TransactionModel.train_no, ""),
                TransactionModel.op_datetime,
                TransactionModel.id,
            ]
        elif sort_key == "passenger":
            order_exprs = [
                func.coalesce(TransactionModel.passenger_id, 0),
                TransactionModel.op_datetime,
                TransactionModel.id,
            ]
        elif sort_key == "final_score":
            order_exprs = [
                func.coalesce(PassengerScoreModel.final_score, 0),
                TransactionModel.op_datetime,
                TransactionModel.id,
            ]
        else:
            order_exprs = [
                TransactionModel.op_datetime,
                TransactionModel.id,
            ]

        if descending:
            return stmt.order_by(*(expr.desc() for expr in order_exprs))
        return stmt.order_by(*(expr.asc() for expr in order_exprs))

    def _score_operation_rows(self, rows: list[dict]) -> list[dict]:
        refund_indexes_by_passenger_day: dict[tuple, list[int]] = defaultdict(list)
        refund_indexes_by_ticket: dict[str, list[int]] = defaultdict(list)
        refund_indexes_by_terminal_hour: dict[tuple, list[int]] = defaultdict(list)

        for idx, item in enumerate(rows):
            tx: Transaction = item["tx"]
            if tx.op_type.value != "refund" or not tx.op_datetime:
                continue

            pid = tx.passenger_id.value if tx.passenger_id else None
            op_day = tx.op_datetime.date()
            refund_indexes_by_passenger_day[(pid, op_day)].append(idx)

            ticket_key = tx.ticket_no or tx.order_no
            if ticket_key:
                refund_indexes_by_ticket[str(ticket_key)].append(idx)

            terminal_key = tx.terminal or tx.point_of_sale or tx.cashdesk
            if terminal_key:
                refund_indexes_by_terminal_hour[
                    (str(terminal_key), op_day, tx.op_datetime.hour)
                ].append(idx)

        cluster_indexes: set[int] = set()
        duplicate_ticket_indexes: set[int] = set()
        terminal_cluster_indexes: set[int] = set()

        for indexes in refund_indexes_by_passenger_day.values():
            if len(indexes) < 3:
                continue

            sorted_indexes = sorted(indexes, key=lambda i: rows[i]["tx"].op_datetime)
            first_dt = rows[sorted_indexes[0]]["tx"].op_datetime
            last_dt = rows[sorted_indexes[-1]]["tx"].op_datetime
            if first_dt and last_dt and (last_dt - first_dt).total_seconds() <= 2 * 60 * 60:
                cluster_indexes.update(sorted_indexes)
                continue

            amount_buckets: dict[tuple, list[int]] = defaultdict(list)
            for idx in sorted_indexes:
                tx = rows[idx]["tx"]
                amount_bucket = round((tx.amount or 0) / 500) * 500
                route_key = tx.route or f"{tx.dep_station or ''}->{tx.arr_station or ''}" or tx.train_no
                amount_buckets[(amount_bucket, route_key)].append(idx)
            for bucket_indexes in amount_buckets.values():
                if len(bucket_indexes) >= 3:
                    cluster_indexes.update(bucket_indexes)

        for indexes in refund_indexes_by_ticket.values():
            if len(indexes) > 1:
                duplicate_ticket_indexes.update(indexes)

        for indexes in refund_indexes_by_terminal_hour.values():
            if len(indexes) >= 5:
                terminal_cluster_indexes.update(indexes)

        scored: list[dict] = []
        for idx, item in enumerate(rows):
            tx: Transaction = item["tx"]
            reasons: list[str] = []
            score = 0
            is_refund = tx.op_type.value == "refund"

            minutes_to_dep = None
            if tx.dep_datetime and tx.op_datetime:
                minutes_to_dep = (tx.dep_datetime - tx.op_datetime).total_seconds() / 60

            has_intrinsic_signal = False

            if is_refund and idx in cluster_indexes:
                score += 55
                has_intrinsic_signal = True
                reasons.append("Несколько похожих возвратов за день в близкий промежуток")

            if is_refund and idx in duplicate_ticket_indexes:
                score += 70
                has_intrinsic_signal = True
                reasons.append("Повторный возврат по одному билету/заказу")

            if is_refund and idx in terminal_cluster_indexes:
                score += 35
                has_intrinsic_signal = True
                reasons.append("Кластер возвратов на одном терминале за час")

            if is_refund and minutes_to_dep is not None and minutes_to_dep >= 0:
                if minutes_to_dep <= 60 and (has_intrinsic_signal or item["seat_blocking_flag"]):
                    score += 30
                    reasons.append("Возврат менее чем за час до отправления")
                elif minutes_to_dep <= 6 * 60 and has_intrinsic_signal:
                    score += 20
                    reasons.append("Возврат менее чем за 6 часов до отправления")
                elif minutes_to_dep <= 24 * 60 and has_intrinsic_signal:
                    score += 10
                    reasons.append("Возврат в последние сутки до отправления")

            if is_refund and tx.amount >= 50000 and has_intrinsic_signal:
                score += 15
                reasons.append("Крупная сумма возврата внутри паттерна")

            if self._identity_is_suspicious(tx, item):
                score += 30 if has_intrinsic_signal else 25
                has_intrinsic_signal = True
                reasons.append("Подозрительные или неполные данные пассажира")

            passenger_band = item["passenger_band"]
            passenger_score = item["passenger_score"]
            if has_intrinsic_signal:
                if passenger_band == RiskBand.critical.value or passenger_score >= 80:
                    score += 20
                    reasons.append("Пассажир уже в critical risk")
                elif passenger_band == RiskBand.high.value or passenger_score >= 55:
                    score += 12
                    reasons.append("Пассажир уже в high risk")

            if is_refund and not has_intrinsic_signal:
                score = min(score, 25)
                reasons = reasons[:1] or ["Обычный единичный возврат без риск-паттерна"]

            operation_score = max(0, min(100, score))
            operation_band = self._operation_band(operation_score)
            scored.append(
                {
                    **item,
                    "operation_score": operation_score,
                    "operation_band": operation_band,
                    "operation_reasons": reasons[:4],
                }
            )
        return scored

    @staticmethod
    def _identity_is_suspicious(tx: Transaction, item: dict) -> bool:
        fio = (tx.fio or "").upper()
        has_placeholder = any(token in fio for token in ("TEST", "ТЕСТ", "UNKNOWN", "XXX", "000000", "QWERTY"))
        missing_identity = not (tx.iin or tx.doc_no or tx.phone)
        return bool(
            has_placeholder
            or (missing_identity and (tx.fio is None or len(tx.fio.strip()) < 8))
            or item["fio_fake_score"] >= 6
        )

    @staticmethod
    def _operation_band(score: int) -> RiskBand:
        if score >= 85:
            return RiskBand.critical
        if score >= 65:
            return RiskBand.high
        if score >= 40:
            return RiskBand.medium
        return RiskBand.low

    @staticmethod
    def _sort_scored_operations(items: list[dict], sort_by: str, sort_order: str) -> list[dict]:
        reverse = sort_order.lower() != "asc"
        band_rank = {
            RiskBand.critical: 4,
            RiskBand.high: 3,
            RiskBand.medium: 2,
            RiskBand.low: 1,
        }

        def rank(item: dict) -> int:
            return band_rank.get(item["operation_band"], 0)

        def tx_id(item: dict) -> int:
            return item["tx"].id.value if item["tx"].id else 0

        def passenger_id(item: dict) -> int:
            return item["tx"].passenger_id.value if item["tx"].passenger_id else 0

        key_map = {
            "risk_score": lambda item: (
                item["operation_score"],
                rank(item),
                item["passenger_score"],
                item["tx"].op_datetime,
                tx_id(item),
            ),
            "risk_band": lambda item: (
                rank(item),
                item["operation_score"],
                item["passenger_score"],
                item["tx"].op_datetime,
                tx_id(item),
            ),
            "final_score": lambda item: (
                item["passenger_score"],
                item["operation_score"],
                rank(item),
                item["tx"].op_datetime,
                tx_id(item),
            ),
            "date": lambda item: (item["tx"].op_datetime, tx_id(item)),
            "amount": lambda item: (item["tx"].amount, item["tx"].op_datetime, tx_id(item)),
            "train_no": lambda item: (item["tx"].train_no or "", item["tx"].op_datetime, tx_id(item)),
            "passenger": lambda item: (passenger_id(item), item["tx"].op_datetime, tx_id(item)),
        }
        key_func = key_map.get(sort_by, key_map["risk_score"])
        return sorted(items, key=key_func, reverse=reverse)
