import re
from collections import Counter

from sqlalchemy import String, case, cast, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert

from app.domain.passenger.entity import Passenger, PassengerIdentitySummary
from app.domain.passenger.repository import IPassengerRepository
from app.domain.passenger.vo import PassengerId, RiskBand
from app.domain.pagination import CursorPaginationParams, CursorPaginationResult
from app.infrastructure.db.cursor_pagination import CursorPage, encode_cursor, decode_cursor
from app.infrastructure.db.mappers.passenger import PassengerMapper, PassengerScoreMapper
from app.infrastructure.db.models.passenger import PassengerModel
from app.infrastructure.db.models.passenger_scores import PassengerScoreModel
from app.infrastructure.db.models.transaction import TransactionModel
from app.infrastructure.db.repos.base import BaseSQLAlchemyRepo


class PassengerRepositoryImpl(IPassengerRepository, BaseSQLAlchemyRepo):

    async def get_by_id(self, passenger_id: PassengerId) -> Passenger | None:
        stmt = select(PassengerModel).where(PassengerModel.id == passenger_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        passenger = PassengerMapper.to_domain(model)
        await self._load_score(passenger)
        await self._load_features(passenger)
        await self._load_identity_summary(passenger)
        return passenger

    async def get_all(
        self,
        risk_band: RiskBand | None = None,
        search: str | None = None,
        sort_by: str = "risk_band",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Passenger]:
        stmt = select(PassengerModel).join(
            PassengerScoreModel,
            PassengerModel.id == PassengerScoreModel.passenger_id,
            isouter=True,
        )

        stmt = self._apply_search(stmt, search)

        if risk_band is not None:
            stmt = stmt.where(PassengerScoreModel.risk_band == risk_band.value)

        stmt = self._apply_sort(stmt, sort_by, sort_order)

        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        passengers = [PassengerMapper.to_domain(m) for m in result.scalars().all()]

        await self._load_scores_bulk(passengers)
        await self._load_features_bulk(passengers)
        return passengers

    async def get_all_cursor(
        self,
        risk_band: RiskBand | None = None,
        search: str | None = None,
        sort_by: str = "risk_band",
        sort_order: str = "desc",
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[Passenger]:
        """Cursor-based pagination (O(1) instead of O(n) offset)."""
        stmt = select(PassengerModel).join(
            PassengerScoreModel,
            PassengerModel.id == PassengerScoreModel.passenger_id,
            isouter=True,
        )

        stmt = self._apply_search(stmt, search)

        if risk_band is not None:
            stmt = stmt.where(PassengerScoreModel.risk_band == risk_band.value)

        if sort_by in {"risk", "risk_score", "final_score"}:
            order_col = PassengerScoreModel.final_score
        elif sort_by == "date":
            order_col = PassengerModel.last_seen_at
        elif sort_by == "fake_fio":
            order_col = PassengerModel.fake_fio_score
        elif sort_by == "name":
            order_col = PassengerModel.fio_clean
        else:
            order_col = PassengerScoreModel.final_score

        if cursor:
            pk_str, sv_str = decode_cursor(cursor)
            pk = int(pk_str)
            if sort_order == "desc":
                stmt = stmt.where(
                    (order_col < float(sv_str)) |
                    ((order_col == float(sv_str)) & (PassengerModel.id < pk))
                )
                stmt = stmt.order_by(order_col.desc(), PassengerModel.id.desc())
            else:
                stmt = stmt.where(
                    (order_col > float(sv_str)) |
                    ((order_col == float(sv_str)) & (PassengerModel.id > pk))
                )
                stmt = stmt.order_by(order_col.asc(), PassengerModel.id.asc())
        else:
            if sort_order == "desc":
                stmt = stmt.order_by(order_col.desc())
            else:
                stmt = stmt.order_by(order_col.asc())

        stmt = stmt.limit(limit + 1)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        has_more = len(models) > limit
        models = models[:limit]

        passengers = [PassengerMapper.to_domain(m) for m in models]
        await self._load_scores_bulk(passengers)
        await self._load_features_bulk(passengers)

        next_cursor = None
        if has_more and passengers:
            last = passengers[-1]
            sort_val = (
                last.score.final_score if last.score else 0
                if sort_by == "risk_score" else last.last_seen_at
                if sort_by == "date" else last.fake_fio_score
                if sort_by == "fake_fio" else last.fio_clean
            )
            next_cursor = encode_cursor(last.id.value, sort_val)

        return CursorPage(
            items=passengers,
            next_cursor=next_cursor,
            prev_cursor=cursor,
            has_more=has_more,
        )

    async def count(self, risk_band: RiskBand | None = None, search: str | None = None) -> int:
        stmt = select(func.count(PassengerModel.id))

        stmt = self._apply_search(stmt, search)

        if risk_band is not None:
            # LEFT JOIN to include passengers without scores, then filter by risk_band
            stmt = stmt.join(
                PassengerScoreModel,
                PassengerModel.id == PassengerScoreModel.passenger_id,
                isouter=True,  # LEFT JOIN
            ).where(PassengerScoreModel.risk_band == risk_band.value)

        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def count_by_date_range(self, date_from, date_to) -> int:
        from datetime import datetime
        stmt = (
            select(func.count(PassengerModel.id))
            .where(PassengerModel.first_seen_at >= date_from)
            .where(PassengerModel.first_seen_at <= date_to)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def count_all_risk_bands(self) -> dict[str, int]:
        """Get counts for all risk bands in a single query (optimized for dashboards)."""
        stmt = select(
            PassengerScoreModel.risk_band,
            func.count(PassengerScoreModel.passenger_id).label("count")
        ).group_by(PassengerScoreModel.risk_band)

        result = await self._session.execute(stmt)
        counts_by_band = {row[0].value: row[1] for row in result.all()}

        # Ensure all risk bands have an entry (even if 0)
        all_bands = {
            "critical": counts_by_band.get("critical", 0),
            "high": counts_by_band.get("high", 0),
            "medium": counts_by_band.get("medium", 0),
            "low": counts_by_band.get("low", 0),
        }
        return all_bands

    async def create_passenger(self, passenger: Passenger) -> None:
        model = PassengerMapper.to_model(passenger)
        self._session.add(model)
        await self._session.flush()

    async def create_batch(self, passengers: list[Passenger]) -> None:
        """Bulk create passengers efficiently."""
        if not passengers:
            return
        chunk_size = 5000
        for start in range(0, len(passengers), chunk_size):
            chunk = passengers[start : start + chunk_size]
            rows = [
                {
                    "id": p.id.value,
                    "fio_clean": p.fio_clean,
                    "fake_fio_score": p.fake_fio_score,
                    "first_seen_at": p.first_seen_at,
                    "last_seen_at": p.last_seen_at,
                }
                for p in chunk
            ]
            insert_stmt = insert(PassengerModel).values(rows)
            excluded = insert_stmt.excluded
            stmt = insert_stmt.on_conflict_do_update(
                index_elements=[PassengerModel.id],
                set_={
                    "fio_clean": excluded.fio_clean,
                    "fake_fio_score": func.greatest(
                        PassengerModel.fake_fio_score,
                        excluded.fake_fio_score,
                    ),
                    "first_seen_at": func.least(
                        PassengerModel.first_seen_at,
                        excluded.first_seen_at,
                    ),
                    "last_seen_at": func.greatest(
                        PassengerModel.last_seen_at,
                        excluded.last_seen_at,
                    ),
                },
            )
            await self._session.execute(stmt)

    async def get_existing_ids(self, passenger_ids: list[int]) -> set[int]:
        """Get ALL existing passenger IDs in batches to avoid parameter limit."""
        if not passenger_ids:
            return set()

        existing_ids = set()
        # Use chunks to avoid PostgreSQL parameter limit (32767)
        # Each ID is one parameter, so use 10000 per batch to be safe
        chunk_size = 10000

        for i in range(0, len(passenger_ids), chunk_size):
            chunk = passenger_ids[i:i + chunk_size]
            stmt = select(PassengerModel.id).where(PassengerModel.id.in_(chunk))
            result = await self._session.execute(stmt)
            existing_ids.update({row[0].value for row in result.all()})

        return existing_ids

    async def update_batch(self, passengers: list[Passenger]) -> None:
        """Bulk update passenger activity via ON CONFLICT upsert."""
        if not passengers:
            return
        await self.create_batch(passengers)

    async def update_passenger(self, passenger: Passenger) -> None:
        stmt = (
            update(PassengerModel)
            .where(PassengerModel.id == passenger.id)
            .values(
                fio_clean=passenger.fio_clean,
                fake_fio_score=passenger.fake_fio_score,
                last_seen_at=passenger.last_seen_at,
            )
        )
        await self._session.execute(stmt)

    async def delete_passenger(self, passenger_id: PassengerId) -> None:
        from sqlalchemy import delete
        stmt = delete(PassengerModel).where(PassengerModel.id == passenger_id)
        await self._session.execute(stmt)

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _risk_rank_expr():
        return case(
            (PassengerScoreModel.risk_band == RiskBand.critical.value, 4),
            (PassengerScoreModel.risk_band == RiskBand.high.value, 3),
            (PassengerScoreModel.risk_band == RiskBand.medium.value, 2),
            (PassengerScoreModel.risk_band == RiskBand.low.value, 1),
            else_=0,
        )

    @classmethod
    def _apply_sort(cls, stmt, sort_by: str, sort_order: str):
        sort_key = (sort_by or "final_score").lower()
        descending = sort_order != "asc"
        score_expr = func.coalesce(PassengerScoreModel.final_score, 0)
        risk_rank = cls._risk_rank_expr()

        if sort_key in {"risk", "risk_score", "final_score"}:
            order_exprs = [score_expr, risk_rank, PassengerModel.last_seen_at, PassengerModel.id]
        elif sort_key == "risk_band":
            order_exprs = [risk_rank, score_expr, PassengerModel.last_seen_at, PassengerModel.id]
        elif sort_key == "date":
            order_exprs = [PassengerModel.last_seen_at, score_expr, PassengerModel.id]
        elif sort_key == "fake_fio":
            order_exprs = [PassengerModel.fake_fio_score, score_expr, PassengerModel.id]
        elif sort_key == "name":
            order_exprs = [PassengerModel.fio_clean, PassengerModel.id]
        else:
            order_exprs = [score_expr, risk_rank, PassengerModel.last_seen_at, PassengerModel.id]

        if descending:
            return stmt.order_by(*(expr.desc() for expr in order_exprs))
        return stmt.order_by(*(expr.asc() for expr in order_exprs))

    @staticmethod
    def _apply_search(stmt, search: str | None):
        if not search:
            return stmt

        raw = search.strip()
        if not raw:
            return stmt

        plain = raw.lstrip("#").strip()
        fio_like = f"%{re.sub(r'[=]+', ' ', raw)}%"
        raw_like = f"%{raw}%"
        plain_like = f"%{plain or raw}%"
        digits = re.sub(r"\D+", "", raw)
        digit_like = f"%{digits}%"

        if plain.isdigit() and len(plain) >= 16:
            try:
                return stmt.where(PassengerModel.id == PassengerId(int(plain)))
            except ValueError:
                pass

        tx_conditions = [
            TransactionModel.iin.ilike(raw_like),
            TransactionModel.doc_no.ilike(raw_like),
            TransactionModel.phone.ilike(raw_like),
            TransactionModel.ticket_no.ilike(raw_like),
            TransactionModel.order_no.ilike(raw_like),
            TransactionModel.iin.ilike(plain_like),
            TransactionModel.doc_no.ilike(plain_like),
            TransactionModel.phone.ilike(plain_like),
        ]
        if digit_like != "%%":
            tx_conditions.extend(
                [
                    TransactionModel.iin.ilike(digit_like),
                    TransactionModel.phone.ilike(digit_like),
                    TransactionModel.doc_no.ilike(digit_like),
                ]
            )

        tx_match = (
            select(TransactionModel.id)
            .where(TransactionModel.passenger_id == PassengerModel.id)
            .where(or_(*tx_conditions))
            .exists()
        )

        direct_id_conditions = []
        if plain.isdigit():
            try:
                direct_id_conditions.append(PassengerModel.id == PassengerId(int(plain)))
            except ValueError:
                pass

        return stmt.where(
            or_(
                *direct_id_conditions,
                PassengerModel.fio_clean.ilike(fio_like),
                PassengerModel.fio_clean.ilike(raw_like),
                cast(PassengerModel.id, String).ilike(plain_like),
                tx_match,
            )
        )

    async def _load_score(self, passenger: Passenger) -> None:
        stmt = select(PassengerScoreModel).where(
            PassengerScoreModel.passenger_id == passenger.id
        )
        result = await self._session.execute(stmt)
        score_model = result.scalar_one_or_none()
        if score_model:
            passenger.score = PassengerScoreMapper.to_domain(score_model)

    async def _load_features(self, passenger: Passenger) -> None:
        from app.infrastructure.db.models.passenger_features import PassengerFeaturesModel
        from app.infrastructure.db.mappers.passenger import PassengerFeaturesMapper
        stmt = select(PassengerFeaturesModel).where(
            PassengerFeaturesModel.passenger_id == passenger.id
        )
        result = await self._session.execute(stmt)
        feature_model = result.scalar_one_or_none()
        if feature_model:
            passenger.features = PassengerFeaturesMapper.to_domain(feature_model)

    async def _load_identity_summary(self, passenger: Passenger) -> None:
        stmt = (
            select(
                TransactionModel.iin,
                TransactionModel.doc_no,
                TransactionModel.phone,
                TransactionModel.gender,
                TransactionModel.fio,
                TransactionModel.channel,
                TransactionModel.aggregator,
                TransactionModel.terminal,
                TransactionModel.branch,
                TransactionModel.sale_user,
                TransactionModel.carrier,
                TransactionModel.tariff_type,
                TransactionModel.service_class,
                TransactionModel.route,
                TransactionModel.train_no,
                TransactionModel.op_datetime,
            )
            .where(TransactionModel.passenger_id == passenger.id)
            .order_by(TransactionModel.op_datetime.desc())
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        if not rows:
            passenger.identity = PassengerIdentitySummary()
            return

        def column_values(index: int) -> list[str]:
            return [row[index] for row in rows]

        def distinct_count(index: int) -> int:
            return len(set(_clean_profile_value(value) for value in column_values(index)) - {None})

        datetimes = [row[15] for row in rows if row[15] is not None]
        channels = _top_profile_values(column_values(5))
        terminals = _top_profile_values(column_values(7))
        routes = _top_profile_values(column_values(13))

        passenger.identity = PassengerIdentitySummary(
            iin=_first_profile_value(column_values(0)),
            doc_no=_first_profile_value(column_values(1)),
            phone=_first_profile_value(column_values(2)),
            gender=_first_profile_value(column_values(3)),
            raw_fio=_first_profile_value(column_values(4)),
            channels=channels,
            aggregators=_top_profile_values(column_values(6)),
            terminals=terminals,
            branches=_top_profile_values(column_values(8)),
            sale_users=_top_profile_values(column_values(9)),
            carriers=_top_profile_values(column_values(10)),
            tariff_types=_top_profile_values(column_values(11)),
            service_classes=_top_profile_values(column_values(12)),
            routes=routes,
            train_numbers=_top_profile_values(column_values(14)),
            distinct_iin_count=distinct_count(0),
            distinct_doc_count=distinct_count(1),
            distinct_phone_count=distinct_count(2),
            distinct_terminal_count=distinct_count(7),
            distinct_route_count=distinct_count(13),
            first_operation_at=min(datetimes) if datetimes else None,
            last_operation_at=max(datetimes) if datetimes else None,
        )

    async def _load_scores_bulk(self, passengers: list[Passenger]) -> None:
        if not passengers:
            return
        ids = [p.id.value for p in passengers]

        # Split into chunks to avoid parameter limit
        score_map = {}
        chunk_size = 1000

        for i in range(0, len(ids), chunk_size):
            chunk = ids[i:i + chunk_size]
            stmt = select(PassengerScoreModel).where(
                PassengerScoreModel.passenger_id.in_(chunk)
            )
            result = await self._session.execute(stmt)
            for m in result.scalars().all():
                score_map[m.passenger_id.value] = m

        for passenger in passengers:
            score_model = score_map.get(passenger.id.value)
            if score_model:
                passenger.score = PassengerScoreMapper.to_domain(score_model)

    async def _load_features_bulk(self, passengers: list[Passenger]) -> None:
        if not passengers:
            return
        from app.infrastructure.db.models.passenger_features import PassengerFeaturesModel
        from app.infrastructure.db.mappers.passenger import PassengerFeaturesMapper
        ids = [p.id.value for p in passengers]

        # Split into chunks to avoid parameter limit
        feature_map = {}
        chunk_size = 1000

        for i in range(0, len(ids), chunk_size):
            chunk = ids[i:i + chunk_size]
            stmt = select(PassengerFeaturesModel).where(
                PassengerFeaturesModel.passenger_id.in_(chunk)
            )
            result = await self._session.execute(stmt)
            for m in result.scalars().all():
                feature_map[m.passenger_id.value] = m

        for passenger in passengers:
            feature_model = feature_map.get(passenger.id.value)
            if feature_model:
                passenger.features = PassengerFeaturesMapper.to_domain(feature_model)


_EMPTY_PROFILE_VALUES = {"", "-", "—", "nan", "none", "null", "н/д", "нет", "не указан"}


def _clean_profile_value(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _EMPTY_PROFILE_VALUES:
        return None
    return text


def _top_profile_values(values, limit: int = 5) -> list[str]:
    counts: Counter[str] = Counter()
    first_seen: dict[str, int] = {}

    for index, raw_value in enumerate(values):
        value = _clean_profile_value(raw_value)
        if value is None:
            continue
        counts[value] += 1
        first_seen.setdefault(value, index)

    return [
        value
        for value, _ in sorted(
            counts.items(),
            key=lambda item: (-item[1], first_seen[item[0]], item[0]),
        )[:limit]
    ]


def _first_profile_value(values) -> str | None:
    top_values = _top_profile_values(values, limit=1)
    return top_values[0] if top_values else None
