"""ETL Pipeline — оркестратор обработки Excel-загрузок.

Порядок выполнения:
  1. Parse Excel → список RawTransaction
  2. Normalize FIO + build passenger_id
  3. Upsert пассажиров (PassengerRepository)
  4. Bulk insert транзакций (TransactionRepository)
  5. Обновить статус Upload → DONE
  6. Audit log: UPLOAD_COMPLETED
  7. ML scoring запускается вызывающим кодом отдельной фазой

При любой ошибке:
  - Upload → FAILED
  - Audit log с деталями ошибки
  - Транзакция откатывается (вызывающий должен управлять сессией)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.application.etl.excel_parser import ExcelParser, ExcelParseError, RawTransaction
from app.application.etl.fio_cleaner import FioCleaner
from app.application.etl.passenger_id_builder import PassengerIdBuilder
from app.application.etl.streaming_parser import StreamingExcelParser
from app.application.services.audit import AuditService
from app.domain.passenger.entity import Passenger
from app.domain.passenger.repository import IPassengerRepository
from app.domain.passenger.vo import PassengerId
from app.domain.transaction.entity import Transaction
from app.domain.transaction.repository import ITransactionRepository
from app.domain.transaction.vo import TransactionId, OperationType
from app.domain.upload.repository import IUploadRepository
from app.domain.upload.vo import UploadId
from app.domain.user.vo import UserId
from app.application.common.transaction import TransactionManager

logger = logging.getLogger(__name__)
MAX_STORED_PARSE_ERRORS = 1000


@dataclass
class EtlResult:
    """Результат выполнения ETL-пайплайна."""

    upload_id: int
    success: bool
    transactions_loaded: int = 0
    passengers_upserted: int = 0
    parse_errors: list[str] = field(default_factory=list)
    parse_error_count: int = 0
    error: str | None = None

    @property
    def has_errors(self) -> bool:
        return self.parse_error_count > 0 or self.error is not None

    def add_parse_errors(self, errors: list[str]) -> None:
        if not errors:
            return
        self.parse_error_count += len(errors)
        remaining = MAX_STORED_PARSE_ERRORS - len(self.parse_errors)
        if remaining > 0:
            self.parse_errors.extend(errors[:remaining])


class EtlPipeline:
    """Оркестратор ETL-пайплайна для загрузки Excel-файлов.

    Usage::

        pipeline = EtlPipeline(
            transaction_repo=...,
            passenger_repo=...,
            upload_repo=...,
            audit_service=...,
        )
        result = await pipeline.run(upload_id=42, file_bytes=..., user_id=user_id)
    """

    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        passenger_repo: IPassengerRepository,
        upload_repo: IUploadRepository,
        audit_service: AuditService,
        transaction_manager: TransactionManager,
        batch_size: int = 50000,
    ) -> None:
        self._tx_repo = transaction_repo
        self._passenger_repo = passenger_repo
        self._upload_repo = upload_repo
        self._audit = audit_service
        self._tx_manager = transaction_manager
        self._batch_size = batch_size

        self._parser = ExcelParser()
        self._streaming_parser = StreamingExcelParser(chunk_size=batch_size)
        self._fio_cleaner = FioCleaner()
        self._id_builder = PassengerIdBuilder()

    # ── Main entry point ──────────────────────────────────────────────────────

    async def run(
        self,
        upload_id: int,
        filepath: str,
        user_id: UserId,
    ) -> EtlResult:
        """Запускает полный ETL-цикл.

        Вся логика обёрнута в try/except, чтобы при ошибке
        статус upload был корректно проставлен как FAILED.
        """
        result = EtlResult(upload_id=upload_id, success=False)
        uid = UploadId(upload_id)
        uid_str = str(upload_id)

        try:
            logger.info("ETL start: upload_id=%s", upload_id)

            upload = await self._upload_repo.get_by_id(uid)
            if upload:
                upload.mark_processing()
                await self._upload_repo.update_upload(upload)
                await self._tx_manager.commit()

            # 1-4. Stream parse, transform, upsert and insert in bounded chunks.
            # This keeps 100MB+/1M-row workbooks from building giant Python
            # lists and lets already parsed chunks reach the database quickly.
            seen_passenger_ids: set[int] = set()
            async for raw_rows, errors, progress in self._streaming_parser.parse_stream(filepath):
                result.add_parse_errors(errors)
                if not raw_rows:
                    continue

                passengers, tx_list = self._transform(raw_rows, uid, result)
                await self._upsert_passengers_bulk(passengers)
                await self._insert_transactions_batched(tx_list)

                seen_passenger_ids.update(passengers.keys())
                result.passengers_upserted = len(seen_passenger_ids)
                result.transactions_loaded += len(tx_list)

                await self._tx_manager.commit()
                logger.info(
                    "ETL upload_id=%s batch=%s parsed=%s inserted=%s passengers=%s row_errors=%s",
                    upload_id,
                    progress.batch_number,
                    progress.rows_parsed,
                    result.transactions_loaded,
                    result.passengers_upserted,
                    result.parse_error_count,
                )

            if result.transactions_loaded == 0:
                raise ValueError("Файл не содержит данных для загрузки.")

            # 5. Обновить статус Upload → DONE
            upload = await self._upload_repo.get_by_id(uid)
            if upload:
                upload.mark_done()
                await self._upload_repo.update_upload(upload)

            # 6. Audit log
            if result.has_errors:
                 logger.warning("ETL completed with %s row-level errors for upload_id=%s", result.parse_error_count, upload_id)
                 # Выведем первые 5 ошибок для диагностики
                 for err in result.parse_errors[:5]:
                     logger.warning("  Row error example: %s", err)
            
            await self._audit.log_upload_completed(uid_str, user_id)

            await self._tx_manager.commit()

            # Mark success before starting async scoring
            result.success = True
            logger.info(
                "ETL done: upload_id=%s, passengers=%s, transactions=%s, errors=%s",
                upload_id, result.passengers_upserted, result.transactions_loaded, result.parse_error_count
            )

        except ExcelParseError as exc:
            await self._tx_manager.rollback()
            result.error = f"Ошибка формата файла: {exc}"
            await self._fail_upload(uid, uid_str, user_id, result.error)
            logger.warning("ETL parse error upload_id=%s: %s", upload_id, exc)

        except Exception as exc:
            await self._tx_manager.rollback()
            result.error = str(exc)
            await self._fail_upload(uid, uid_str, user_id, result.error)
            logger.exception("ETL fatal error upload_id=%s", upload_id)

        return result

    # ── Steps ─────────────────────────────────────────────────────────────────

    def _parse(self, file_bytes: bytes, result: EtlResult) -> list[RawTransaction]:
        """Шаг 1: парсим Excel, собираем ошибки строк."""
        # load теперь возвращает (список транзакций, список ошибок)
        # Fatal-ошибки (заголовки и т.д.) по-прежнему выбрасывают ExcelParseError
        tx_list, errors = self._parser.load(file_bytes)
        result.add_parse_errors(errors)
        return tx_list

    def _parse_file(self, filepath: str, result: EtlResult) -> list[RawTransaction]:
        """Шаг 1: парсим Excel из файла, собираем ошибки строк."""
        with open(filepath, 'rb') as f:
            file_bytes = f.read()
        return self._parse(file_bytes, result)

    def _transform(
        self, raw_rows: list[RawTransaction], upload_id: UploadId, result: EtlResult
    ) -> tuple[dict[int, Passenger], list[Transaction]]:
        """Шаг 2: нормализация ФИО, построение passenger_id, конвертация в domain."""
        passengers: dict[int, Passenger] = {}
        transactions: list[Transaction] = []

        for raw in raw_rows:
            try:
                # Нормализация ФИО
                fio_clean = self._fio_cleaner.clean(raw.fio)
                fake_score = FioCleaner.fake_fio_score(fio_clean)

                # Построение passenger_id
                try:
                    pid_int = self._id_builder.build(
                        iin=raw.iin,
                        fio_clean=fio_clean,
                        doc_no=raw.doc_no,
                        phone=raw.phone,
                    )
                except ValueError as exc:
                    # Если пассажира совсем нельзя опознать, создаем 'анонимного'
                    logger.debug("Анонимная строка row=%s: %s", raw._row_num, exc)
                    pid_int = self._id_builder._hash_to_int64(f"anonymous:{raw._row_num}:{raw.op_datetime}")
                    fio_clean = fio_clean or "SYSTEM_ANONYMOUS"

                passenger_id = PassengerId(pid_int)

                # Upsert-логика пассажира
                op_dt = raw.op_datetime.replace(tzinfo=UTC) if raw.op_datetime.tzinfo is None else raw.op_datetime
                if pid_int not in passengers:
                    passengers[pid_int] = Passenger.create(
                        passenger_id=pid_int,
                        fio_clean=fio_clean,
                        first_seen_at=op_dt,
                        fake_fio_score=fake_score,
                    )
                else:
                    passengers[pid_int].update_activity(op_dt)

                # Построение transaction_id
                tx_id = self._build_tx_id(raw, upload_id, fio_clean)

                tx = Transaction(
                    id=TransactionId(tx_id),
                    upload_id=upload_id,
                    source=raw.source,
                    op_type=OperationType(raw.op_type),
                    op_datetime=op_dt,
                    dep_datetime=(
                        raw.dep_datetime.replace(tzinfo=UTC)
                        if raw.dep_datetime and raw.dep_datetime.tzinfo is None
                        else raw.dep_datetime
                    ),
                    train_no=raw.train_no,
                    channel=raw.channel,
                    aggregator=raw.aggregator,
                    terminal=raw.terminal,
                    cashdesk=raw.cashdesk,
                    point_of_sale=raw.point_of_sale,
                    amount=raw.amount,
                    fee=raw.fee,
                    fio=raw.fio,
                    iin=raw.iin,
                    doc_no=raw.doc_no,
                    phone=raw.phone,
                    gender=raw.gender,
                    ticket_no=raw.ticket_no,
                    tariff_type=raw.tariff_type,
                    service_class=raw.service_class,
                    branch=raw.branch,
                    sale_user=raw.sale_user,
                    carrier=raw.carrier,
                    settlement_type=raw.settlement_type,
                    order_no=raw.order_no,
                    dep_station=raw.dep_station,
                    arr_station=raw.arr_station,
                    route=raw.route,
                    passenger_id=passenger_id,
                )
                transactions.append(tx)
            except Exception as exc:
                err_msg = f"Строка {raw._row_num}: Ошибка трансформации: {exc}"
                logger.warning(err_msg)
                result.add_parse_errors([err_msg])

        return passengers, transactions

    async def _upsert_passengers(self, passengers: dict[int, Passenger]) -> None:
        """Шаг 3: создать/обновить пассажиров."""
        for passenger in passengers.values():
            existing = await self._passenger_repo.get_by_id(passenger.id)
            if existing is None:
                await self._passenger_repo.create_passenger(passenger)
            else:
                existing.update_activity(passenger.last_seen_at)
                await self._passenger_repo.update_passenger(existing)

    async def _upsert_passengers_bulk(self, passengers: dict[int, Passenger]) -> None:
        """Шаг 3: bulk upsert пассажиров (намного быстрее для больших объемов)."""
        if not passengers:
            return

        # Repository create_batch uses INSERT .. ON CONFLICT DO UPDATE. Avoid a
        # giant "select existing ids" round-trip per chunk.
        await self._passenger_repo.create_batch(list(passengers.values()))

    async def _insert_transactions_batched(self, transactions: list[Transaction]) -> None:
        """Шаг 4: bulk insert транзакций батчами (оптимизировано: отключить триггеры)."""
        if not transactions:
            return

        from sqlalchemy import text

        await self._tx_repo._session.execute(text("SET LOCAL synchronous_commit = off"))
        await self._tx_repo.create_batch(transactions)

    async def _fail_upload(
        self, uid: UploadId, uid_str: str, user_id: UserId, error: str
    ) -> None:
        """Помечает upload как FAILED и пишет в audit."""
        try:
            upload = await self._upload_repo.get_by_id(uid)
            if upload:
                upload.mark_failed(error[:2048])
                await self._upload_repo.update_upload(upload)
        except Exception:
            logger.exception("Не удалось обновить статус upload_id=%s на FAILED", uid_str)

        try:
            await self._audit.log_action(
                action="UPLOAD_FAILED",
                entity_type="upload",
                entity_id=uid_str,
                user_id=user_id,
                meta={"error": error[:500]},
            )
        except Exception:
            logger.exception("Не удалось записать audit log для upload_id=%s", uid_str)

        try:
            await self._tx_manager.commit()
        except Exception:
            logger.exception("Не удалось закоммитить FAILED статус для upload_id=%s", uid_str)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_tx_id(raw: RawTransaction, upload_id: UploadId, fio_clean: str) -> int:
        """Детерминированный ID транзакции.

        Ключ: upload_id + row_num + op_datetime + amount + fio_clean.
        """
        import hashlib
        import struct

        key = (
            f"{upload_id.value}:{raw._row_num}:"
            f"{raw.op_datetime.isoformat()}:{raw.amount}:{fio_clean}"
        )
        digest = hashlib.sha256(key.encode()).digest()
        raw_int = struct.unpack(">Q", digest[:8])[0]
        return raw_int & 0x7FFF_FFFF_FFFF_FFFF
