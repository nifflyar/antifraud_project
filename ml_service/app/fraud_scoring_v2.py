"""Enhanced fake FIO detection with HIGH PRECISION and minimal false positives.

New approach: Only mark as HIGH confidence (8-10) when there's EXTREME evidence
of placeholder/fake identity. Valid names with initials, foreign characters,
and apostrophes are treated as NORMAL.
"""

import re
from typing import List, Tuple


PLACEHOLDER_KEYWORDS = {
    "ТЕСТ", "TEST", "UNKNOWN", "НЕИЗВЕСТНО", "QWERTY", "ЙЦУКЕН",
    "ХХ", "XX", "ООО", "ФИО", "ИНФОРМАЦИЯ", "ИНФОРМ", "ДАННЫЕ",
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

    if len(tokens[0]) < 2:
        return False

    initial_count = sum(1 for t in tokens[1:] if len(t) <= 2)
    return initial_count >= len(tokens) - 1


def fake_fio_score_detailed(
    raw_fio: str | None, fio_clean: str | None
) -> Tuple[int, List[str]]:
    """
    Detect fake/placeholder FIO with HIGH PRECISION (minimizing false positives).

    Returns:
        (score: 0-10, reasons: list of detection reasons)
        0-2: Normal (including initials, foreign names)
        3-4: Minor oddities (suspicious but likely legitimate)
        5-7: Moderate concerns (needs corroboration)
        8-10: High confidence fake/placeholder (extreme evidence)

    Key principle: A single suspicious factor is NOT enough. Require evidence
    of actual placeholder or extremely repeated/garbage patterns.
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

    # 1. PLACEHOLDER KEYWORDS - Highest confidence markers only
    has_placeholder = False
    core_placeholders = {"ФИО", "UNKNOWN", "TEST", "ТЕСТ", "QWERTY", "NAME", "CUSTOMER"}
    for keyword in core_placeholders:
        if keyword in clean:
            score += 9  # Very high - this IS a placeholder
            reasons.append(f"placeholder_keyword:{keyword.lower()}")
            has_placeholder = True
            break

    # Check for multiple weak keywords (multiple weak signals = something's wrong)
    if not has_placeholder:
        weak_keywords = {"ХХ", "XX", "ООО", "ИНФОРМАЦИЯ", "ИНФОРМ", "ДАННЫЕ"}
        weak_matches = [kw for kw in weak_keywords if kw in clean]
        if len(weak_matches) >= 2:  # Multiple weak keywords
            score += 5
            reasons.append(f"multiple_weak_keywords:{','.join(weak_matches)}")
        elif len(weak_matches) == 1 and len(clean) < 5:  # Single weak keyword in very short string
            score += 3
            reasons.append(f"weak_keyword_very_short:{weak_matches[0]}")

    # 2. Extreme repeated zeros (8+ consecutive)
    if re.search(r"0{8,}", text):
        score += 6
        reasons.append("extreme_repeated_zeros_8plus")
    elif re.search(r"0{4,6}", text) and len(clean) <= 8:  # 4-6 zeros in very short string
        score += 3
        reasons.append("repeated_zeros_in_short")

    # 3. Extreme repeated characters (3+ in sequence: ААА, БББ)
    if REPEATED_CHAR_PATTERN.search(clean):
        score += 4
        reasons.append("extreme_repeated_chars_3plus")

    # 4. Mixed Cyrillic/Latin - Be LENIENT with legitimate foreign names
    cyrillic_count = sum(1 for c in clean if ord(c) >= 1040)
    latin_count = sum(1 for c in clean if c.isalpha() and ord(c) < 1040)

    if cyrillic_count > 0 and latin_count > 0:
        # Single apostrophe or dash = legitimate foreign name (О'ДОНЕЛ, ИВАНОВ-СМИТ)
        if "'" in raw_fio or "-" in raw_fio:
            pass  # Legitimate connector, no penalty
        elif latin_count == 1:
            # Single Latin character (like J or R for initial) = completely normal
            pass
        elif latin_count >= 2 and latin_count <= 3 and cyrillic_count >= latin_count:
            # A few Latin chars mixed with Cyrillic = probably legitimate (foreign name)
            score += 1
            reasons.append("minor_mixed_alphabet")
        elif latin_count > 3 or (cyrillic_count < 2 and latin_count >= 2):
            # Heavy Latin with minimal Cyrillic = data corruption or intentional mixing
            score += 3
            reasons.append("heavy_mixed_alphabet")

    # 5. Numbers in FIO - Strong red flag
    if re.search(r"[0-9]", clean):
        score += 5
        reasons.append("contains_digits")

    # 6. Special characters beyond apostrophe/dash
    special_chars = [c for c in clean if not c.isalpha() and c != " " and c != "-" and c != "'"]
    if len(special_chars) > 5:
        score += 3
        reasons.append("many_special_chars")
    elif len(special_chars) > 2:
        score += 1
        reasons.append("unusual_special_chars")

    # 7. Structural problems
    if len(clean) < 3:
        # "А", "АА", "AB" = too short
        score += 5
        reasons.append("extremely_short_name")
    elif len(clean) < 5:
        # 3-4 chars: only flag if it's NOT valid initials
        if not _has_valid_initials(tokens):
            score += 2
            reasons.append("short_name_invalid_structure")

    # 8. Token count
    if len(tokens) == 0 or (len(tokens) == 1 and len(tokens[0]) < 2):
        score += 3
        reasons.append("no_valid_name_structure")
    elif len(tokens) > 5:
        # More tokens is unusual but can happen with double names/connectors
        score += 1
        reasons.append("unusually_many_tokens")

    # 9. VALID INITIALS PATTERN - Strong signal of legitimacy
    # This is a common legitimate pattern, not suspicious
    if len(tokens) >= 2 and _has_valid_initials(tokens) and not has_placeholder:
        score = max(0, score - 4)
        if score <= 1:
            reasons.append("valid_initials_normal_pattern")
        else:
            reasons.append("initials_present_slightly_reduces_score")

    # 10. Extreme single-character repetition like "А А А А"
    if re.search(r"[А-Я]\s+[А-Я]\s+[А-Я]\s+[А-Я]", clean):
        score += 5
        reasons.append("extreme_single_char_repetition")

    # 11. Equals signs or other garbage (А=С ИИ000)
    if "=" in raw_fio:
        score += 4
        reasons.append("equals_sign_in_name")

    # Ensure score is in [0, 10]
    final_score = min(10, max(0, score))

    # Assign interpretation
    if not reasons:
        if final_score <= 2:
            reasons.append("normal_fio")
        elif final_score <= 4:
            reasons.append("minor_oddities")
        elif final_score <= 7:
            reasons.append("moderate_concerns")
        else:
            reasons.append("high_confidence_fake")

    return final_score, reasons


def categorize_fake_fio_risk(score: int) -> str:
    """Convert fake FIO score to risk category.

    Updated thresholds to minimize false positives:
    - 0-2: normal (including names with initials, foreign names)
    - 3-4: minor (suspicious but likely legitimate)
    - 5-7: suspicious (needs corroboration from other signals)
    - 8-10: high_confidence_fake (extreme evidence)
    """
    if score <= 2:
        return "normal"
    elif score <= 4:
        return "minor"
    elif score <= 7:
        return "suspicious"
    else:
        return "high_confidence_fake"
