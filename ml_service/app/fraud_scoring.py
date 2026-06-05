"""Enhanced fake FIO detection with nuanced scoring and reasoning."""

import re
from typing import List, Tuple


PLACEHOLDER_KEYWORDS = {
    "ТЕСТ", "TEST", "UNKNOWN", "НЕИЗВЕСТНО", "QWERTY", "ЙЦУКЕН",
    "ХХ", "XX", "ООО", "ФИО", "ИНФОРМАЦИЯ", "ИНФОРМ", "ДАННЫЕ", "ДАННЫЕ",
    "CUSTOMER", "CUSTOMER NAME", "NAME"
}

REPEATED_CHAR_PATTERN = re.compile(r"([А-ЯA-Z])\1{2,}")  # 3+ same chars
REPEATED_SHORT_TOKEN_PATTERN = re.compile(r"\b([А-ЯA-Z])\1\b")


def _has_valid_initials(tokens: List[str]) -> bool:
    """Check if tokens contain valid initials (1-letter tokens after surname).

    Valid patterns:
    - "ТАКИБАЕВА А К" (surname + 2 initials)
    - "ИВАНОВ И И" (surname + 2 initials)
    - "SMITH J R" (English equivalent)
    """
    if len(tokens) < 3:
        return False

    # First token should be 2+ chars (surname)
    if len(tokens[0]) < 2:
        return False

    # Rest should be mostly 1-2 character initials
    initial_count = sum(1 for t in tokens[1:] if len(t) <= 2)
    return initial_count >= len(tokens) - 1


def fake_fio_score_detailed(
    raw_fio: str | None, fio_clean: str | None
) -> Tuple[int, List[str]]:
    """
    Detect fake/placeholder FIO with nuanced scoring.

    Returns:
        (score: 0-10, reasons: list of detection reasons)
        0-2: Normal (possibly with initials)
        3-5: Minor oddities
        6-7: Suspicious, needs review
        8-10: High confidence fake/placeholder
    """
    if not raw_fio:
        return 10, ["no_fio_provided"]

    if not fio_clean:
        return 8, ["empty_after_cleaning"]

    score = 0
    reasons: List[str] = []

    text = raw_fio.upper().strip()
    clean = fio_clean.upper().strip()
    tokens = [t for t in clean.split() if t and t != "-"]

    # 1. Check for placeholder keywords. These are high-confidence fake
    # identity markers and must not be cancelled by "surname + initials" logic.
    has_placeholder = False
    for keyword in PLACEHOLDER_KEYWORDS:
        if keyword in clean:
            score += 8 if keyword in {"ФИО", "UNKNOWN", "TEST", "ТЕСТ", "QWERTY", "NAME", "CUSTOMER"} else 5
            reasons.append(f"placeholder_keyword:{keyword.lower()}")
            has_placeholder = True
            break

    # 2. Check for repeated 0s or garbage patterns
    if "000000" in text or "0000" in clean:
        score += 3
        reasons.append("repeated_zeros")

    # 3. Check for repeated characters (АА, ИИ, etc.)
    if REPEATED_CHAR_PATTERN.search(clean):
        score += 2
        reasons.append("repeated_characters")
    elif REPEATED_SHORT_TOKEN_PATTERN.search(clean):
        score += 1
        reasons.append("repeated_short_initial_token")

    # 4. Check for mixed Cyrillic/Latin in suspicious way
    cyrillic_count = sum(1 for c in clean if ord(c) >= 1040)  # Cyrillic range
    latin_count = sum(1 for c in clean if c.isalpha() and ord(c) < 1040)
    if cyrillic_count > 0 and latin_count > 0:
        # Allow Latin for names like "О'ДОНNEL" or single Latin char
        if latin_count > 2 or (cyrillic_count < 2 and latin_count >= 2):
            score += 3
            reasons.append("suspicious_mixed_alphabet")

    # 5. Check for impossible patterns: numbers in FIO name (not in extracted IIN)
    if re.search(r"[0-9]", clean):
        score += 3
        reasons.append("contains_digits")

    # 6. Check for too many special characters
    special_count = sum(1 for c in clean if not c.isalpha() and c != " " and c != "-")
    if special_count > 3:
        score += 2
        reasons.append("too_many_special_chars")

    # 7. Check for extremely short FIO (but be careful with initials)
    if len(clean) < 5:
        # "А К" type initials-only (no surname) is suspicious
        if not _has_valid_initials(tokens) or len(tokens[0]) <= 2:
            score += 2
            reasons.append("extremely_short_fio")

    # 8. Check for too few tokens (no surname)
    if len(tokens) < 2:
        # Single token might be OK if it's 3+ chars (just a surname)
        if len(tokens[0]) < 3:
            score += 2
            reasons.append("no_proper_name_structure")
    elif len(tokens) > 4:
        # More than 4 tokens is unusual
        score += 1
        reasons.append("unusual_token_count")

    # 9. If we detect valid initials, reduce score by 2-3 (they're normal)
    if len(tokens) >= 3 and _has_valid_initials(tokens) and not has_placeholder:
        score = max(0, score - 3)
        if score <= 2:
            reasons.append("valid_initials_pattern")

    # 10. Suspicious pattern: single char repeated in FIO ("А=С ИИ000000000000")
    if "=" in raw_fio or re.search(r"[А-Я]\s*[А-Я]\s*[А-Я]\s*[А-Я]", clean):
        if text.count("=") > 2 or re.search(r"[А-Я]{1}(?:\s+[А-Я]){3,}", clean):
            score += 3
            reasons.append("suspicious_pattern")

    # Ensure score is in [0, 10]
    final_score = min(10, max(0, score))

    # If no reasons found and score is low, mark as normal
    if not reasons:
        if final_score <= 2:
            reasons.append("normal_fio")
        elif final_score <= 5:
            reasons.append("minor_anomalies")
        else:
            reasons.append("multiple_suspicious_signals")

    return final_score, reasons


def categorize_fake_fio_risk(score: int) -> str:
    """Categorize fake FIO score into risk band."""
    if score <= 2:
        return "normal"
    elif score <= 5:
        return "minor"
    elif score <= 7:
        return "suspicious"
    else:
        return "high_confidence_fake"
