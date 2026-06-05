"""Детерминированный строитель идентификатора пассажира.

Стратегия (по приоритету):
  1. IIN (ИИН) — если не пуст, используем как ключ напрямую
  2. fio_clean + doc_no — если оба есть
  3. fio_clean — только имя (ненадежно, но лучше ничего)

Из ключа строится int64 через xxhash для совместимости с BigInteger PK.
"""
from __future__ import annotations

import hashlib
import struct


# Namespace UUID для UUID5 (константа проекта)
_NAMESPACE = b"antifrode_passenger_v1"


class PassengerIdBuilder:
    """Строит детерминированный passenger_id (int64) из доступных данных.

    Один и тот же набор данных всегда даёт один и тот же ID,
    что позволяет безопасно делать upsert при повторных загрузках.

    Example::

        builder = PassengerIdBuilder()
        pid = builder.build(iin="123456789012", fio_clean="ИВАНОВ ИВАН", doc_no=None)
        # всегда один и тот же int
    """

    def build(
        self,
        iin: str | None,
        fio_clean: str,
        doc_no: str | None = None,
        phone: str | None = None,
    ) -> int:
        """Возвращает детерминированный int64 passenger_id.

        Args:
            iin: ИИН (12 цифр для Казахстана). Используется первым.
            fio_clean: Нормализованное ФИО (уже прошедшее через FioCleaner).
            doc_no: Серия и номер документа.

        Returns:
            Положительный int64, уникальный для данной комбинации.
        """
        key = self._build_key(iin, fio_clean, doc_no, phone)
        return self._hash_to_int64(key)

    # ── Internals ─────────────────────────────────────────────────────────────

    @staticmethod
    def _build_key(
        iin: str | None,
        fio_clean: str,
        doc_no: str | None,
        phone: str | None,
    ) -> str:
        """Строит строчный ключ по стратегии приоритетов."""
        iin_clean = iin.strip() if iin else ""
        fio = fio_clean.strip().upper()
        doc = doc_no.strip().upper() if doc_no else ""
        ph = phone.strip() if phone else ""

        # Приоритет 1: IIN
        if iin_clean and len(iin_clean) >= 10:
            return f"iin:{iin_clean}"

        # Приоритет 2: ФИО + документ
        if fio and doc:
            return f"fio_doc:{fio}|{doc}"

        # Приоритет 3: ФИО + телефон
        if fio and ph:
            return f"fio_ph:{fio}|{ph}"

        # Приоритет 4: только ФИО (менее надёжно)
        if fio:
            return f"fio:{fio}"

        # Крайний случай — будет дубль, но лучше, чем упасть
        raise ValueError(
            "Недостаточно данных для построения passenger_id: "
            f"iin={iin!r}, fio_clean={fio_clean!r}, doc_no={doc_no!r}, phone={phone!r}"
        )

    @staticmethod
    def _hash_to_int64(key: str) -> int:
        """SHA-256(namespace + key) → первые 8 байт → unsigned int64 → сжать до позитивного int63."""
        data = _NAMESPACE + b":" + key.encode("utf-8")
        digest = hashlib.sha256(data).digest()
        # Берём первые 8 байт как unsigned big-endian int64
        raw = struct.unpack(">Q", digest[:8])[0]
        # Маскируем старший бит, чтобы оставалось в диапазоне PostgreSQL bigint (0 ... 2^63-1)
        return raw & 0x7FFF_FFFF_FFFF_FFFF
