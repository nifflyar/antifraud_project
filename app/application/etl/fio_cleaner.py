"""Нормализатор ФИО пассажиров.

Цель: привести разные написания одного человека к единому ключу,
чтобы детерминировано строить passenger_id.
"""
from __future__ import annotations

import re
import unicodedata

# Таблица транслитерации ru → lat (упрощённая)
_RU_TO_LAT: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
    # Казахские буквы
    "ә": "ae", "ғ": "gh", "қ": "q", "ң": "ng", "ө": "oe",
    "ұ": "u", "ү": "ue", "і": "i", "һ": "h",
}

# Токены, которые считаются мусором (не имя)
_NOISE_TOKENS: frozenset[str] = frozenset(
    {"г", "гр", "господин", "госпожа", "mr", "mrs", "ms", "dr", "none", "null", "-", ""}
)

# Regex: только буквы (кириллица + латиница + казахские) и пробелы
_ALLOWED = re.compile(r"[^а-яёәғқңөұүіһa-z\s]", re.IGNORECASE)


class FioCleaner:
    """Нормализует ФИО пассажира для детерминированной идентификации.

    Алгоритм:
    1. Unicode NFC normalization → strip
    2. Lowercase
    3. Удаление мусорных символов (знаки препинания, цифры)
    4. Удаление шумовых токенов (г-н, mr, etc.)
    5. Нормализация пробелов
    6. Опциональная транслитерация кириллицы

    Example::

        cleaner = FioCleaner()
        key = cleaner.clean("ИВАНОВ  Иван  Иванович")
        # -> "ИВАНОВ ИВАН ИВАНОВИЧ"
    """

    def __init__(self, transliterate: bool = False) -> None:
        """
        Args:
            transliterate: Если True, кириллица → латиница.
                Полезно при сравнении с данными из латинских систем.
        """
        self._transliterate = transliterate

    def clean(self, raw_fio: str | None) -> str:
        """Нормализует одно ФИО. Возвращает UPPER-case строку."""
        if not raw_fio:
            return ""

        # 1. NFC + strip
        s = unicodedata.normalize("NFC", raw_fio).strip()

        # 2. Lowercase для обработки
        s = s.lower()

        # 3. Убрать мусорные символы (оставить буквы + пробелы)
        s = _ALLOWED.sub(" ", s)

        # 4. Разбить на токены, убрать шумовые
        tokens = [t for t in s.split() if t not in _NOISE_TOKENS]

        if not tokens:
            return ""

        # 5. Нормализация пробелов
        s = " ".join(tokens)

        # 6. Транслитерация (опционально)
        if self._transliterate:
            s = self._to_latin(s)

        # 7. Возвращаем в UPPERCASE как канонический ключ
        return s.upper()

    def clean_batch(self, raw_fios: list[str | None]) -> list[str]:
        """Пакетная нормализация."""
        return [self.clean(fio) for fio in raw_fios]

    @staticmethod
    def fake_fio_score(fio_clean: str) -> float:
        """Эвристическая оценка вероятности фиктивного ФИО (0.0 – 1.0).
        
        Синхронизировано с Notebook 13:
        - Junk: aaa, iii, test, qwerty
        - Unique chars: < 4
        - Length: < 5
        """
        if not fio_clean:
            return 1.0

        fio_lower = fio_clean.lower()
        score = 0.0

        # 1. Placeholder/junk tokens. "ФИО" is a field label, not a surname.
        junk_tokens = [
            "aaa", "иии", "test", "qwerty", "test01", "тест",
            "unknown", "неизвестно", "фио", "customer", "name",
        ]
        if any(token in fio_lower for token in junk_tokens):
            score += 0.8

        # 2. Мало уникальных букв (энтропия)
        unique_chars = {ch for ch in fio_lower if ch.isalpha()}
        if len(unique_chars) <= 3:
            score += 0.7

        # 3. Структурные признаки (бэкенд)
        tokens = fio_clean.split()
        if len(tokens) < 2:
            score += 0.4
        if len(tokens) > 1 and len(set(tokens)) == 1:
            score += 0.8
        if tokens and tokens[0].lower() in {"фио", "test", "unknown", "name", "customer"}:
            score += 0.8
        if any(len(t) == 2 and len(set(t.lower())) == 1 for t in tokens[1:]):
            score += 0.2
        
        # 4. Общая длина
        total_len = sum(len(t) for t in tokens)
        if total_len < 5:
            score += 0.5

        return min(score, 1.0)

    @staticmethod
    def _to_latin(s: str) -> str:
        result: list[str] = []
        for ch in s:
            result.append(_RU_TO_LAT.get(ch, ch))
        return "".join(result)
