"""Contextual validation to catch legitimate scenarios and prevent false positives."""

import pandas as pd
import numpy as np


def apply_contextual_validation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply business logic rules to identify legitimate scenarios and cap scores.

    This is the KEY to reducing false positives - real fraudsters have
    MULTIPLE coordinated signals, while legitimate passengers have isolated issues.

    Args:
        df: DataFrame with scores and features

    Returns:
        DataFrame with contextual_cap applied to final_score
    """
    df = df.copy()
    df["contextual_cap"] = 100  # Default: no cap

    # Scenario A: Booking Error (many tickets, many returns, no fraud signals)
    booking_error = (
        (df["total_tickets"] >= 5)
        & (df["refund_cnt"] >= 1)
        & (df["refund_share"] >= 0.4)  # At least 40% returns
        & (df["seat_blocking_score"] < 50)  # No seat blocking
        & (df["rapid_cancel_cnt"] <= 1)    # No rapid cancels
        & (df["technical_cancel_cnt"] <= 1)
        & (df["fio_fake_score_max"] <= 3)  # No severe identity issues
        & (df["terminal_count"] <= 2)      # Single or dual terminal
    )
    df.loc[booking_error, "contextual_cap"] = 35

    # Scenario B: Legitimate corrections (few tickets, few returns, normal name)
    legitimate_corrections = (
        (df["total_tickets"] <= 5)
        & (df["refund_cnt"] <= 2)
        & (df["rapid_cancel_cnt"] == 0)
        & (df["technical_cancel_cnt"] == 0)
        & (df["fio_fake_score_max"] <= 3)
        & (df["seat_blocking_score"] < 30)
        & (df["terminal_count"] <= 2)
        & (df.get("max_tickets_same_depday", 5) <= 4)
    )
    df.loc[legitimate_corrections, "contextual_cap"] = 20

    # Scenario C: Tourist group or bulk purchase
    # (many tickets, NO coordinated fraud signals)
    tourist_group = (
        (df["total_tickets"] >= 20)
        & (df["total_ops"] >= 30)
        & (df["refund_cnt"] <= 3)  # Few returns (normal for group bookings)
        & (df["seat_blocking_score"] < 50)  # Not blocking seats
        & (df["rapid_cancel_cnt"] <= 1)
        & (df["fio_fake_score_max"] <= 3)
        & ~(
            # AND NOT multiple high-risk signals
            (df.get("suspicious_refund_pattern_cnt", 0) >= 3)
            | (df["terminal_count"] >= 8)
        )
    )
    df.loc[tourist_group, "contextual_cap"] = 40

    # Scenario D: Foreign name (legitimate mixed alphabet)
    # Names like О'ДОНЕЛ, ИВАНОВ-СМИТ are normal
    foreign_name = (
        (df["fio_fake_score_max"] >= 3)
        & (df["fio_fake_score_max"] <= 5)
        & (df["total_tickets"] <= 5)  # Low volume
        & (df["refund_cnt"] <= 1)
        & (df["seat_blocking_score"] < 30)
    )
    df.loc[foreign_name, "contextual_cap"] = 25

    # Scenario D2: Isolated fake/placeholder FIO without behavioral fraud.
    # A bad name is a data-quality/identity review signal, not by itself proof of
    # fraud. Escalation requires refund abuse, seat blocking, terminal spread,
    # identity consistency issues, or repeated high-volume behavior.
    isolated_identity_issue = (
        (df["fio_fake_score_max"] >= 8)
        & (df["refund_cnt"] == 0)
        & (df.get("suspicious_refund_pattern_cnt", 0) == 0)
        & (df["total_tickets"] <= 10)
        & (df.get("max_tickets_same_depday", 0) <= 4)
        & (df["seat_blocking_score"] < 30)
        & (df["rapid_cancel_cnt"] == 0)
        & (df["technical_cancel_cnt"] == 0)
        & (df["terminal_count"] <= 2)
        & (df.get("consistency_risk_score", 0) < 20)
    )
    df.loc[isolated_identity_issue, "contextual_cap"] = 35

    # Scenario D3: Placeholder identity plus simple activity, but still no
    # actionable fraud behavior. Keep it reviewable, not high/critical.
    identity_without_abuse = (
        (df["fio_fake_score_max"] >= 8)
        & (df["refund_cnt"] <= 1)
        & (df.get("suspicious_refund_pattern_cnt", 0) == 0)
        & (df["seat_blocking_score"] < 50)
        & (df["rapid_cancel_cnt"] <= 1)
        & (df["technical_cancel_cnt"] <= 1)
        & (df["terminal_count"] <= 3)
        & (df.get("consistency_risk_score", 0) < 20)
    )
    df.loc[identity_without_abuse, "contextual_cap"] = np.minimum(
        df.loc[identity_without_abuse, "contextual_cap"], 45
    )

    # Scenario E: Single isolated signal without corroboration
    single_high_refund_cnt = (
        (df["refund_cnt"] >= 3)
        & (df["refund_cnt"] <= 4)
        & (df.get("suspicious_refund_pattern_cnt", 0) == 0)  # Not organized
        & (df["rapid_cancel_cnt"] == 0)
        & (df["technical_cancel_cnt"] == 0)
        & (df["fio_fake_score_max"] <= 3)
        & (df["seat_blocking_score"] < 50)
        & (df["terminal_count"] <= 2)
    )
    df.loc[single_high_refund_cnt, "contextual_cap"] = 40

    # Scenario F: Moderate night activity (not necessarily suspicious)
    # Only flag if ALSO has high volume and other signals
    legitimate_night_activity = (
        (df.get("night_share", 0) >= 0.3)
        & (df.get("total_tickets", 0) < 10)  # Low volume
        & (df["refund_cnt"] <= 2)
        & (df["seat_blocking_score"] < 50)
        & (df["fio_fake_score_max"] <= 3)
    )
    df.loc[legitimate_night_activity, "contextual_cap"] = 30

    # Apply caps: use minimum of current final_score and contextual_cap
    df["final_score"] = np.minimum(df["final_score"], df["contextual_cap"])

    return df


def get_validation_reason(row: pd.Series) -> str | None:
    """
    Determine which contextual validation rule applies to this passenger.
    Returns the reason if capped, None otherwise.
    """
    # Check each scenario in order
    if (row["total_tickets"] >= 5 and row["refund_cnt"] >= 1
            and row["refund_share"] >= 0.4 and row["seat_blocking_score"] < 50):
        return "booking_error_pattern"

    if (row["total_tickets"] <= 5 and row["refund_cnt"] <= 2
            and row["rapid_cancel_cnt"] == 0 and row["fio_fake_score_max"] <= 3):
        return "legitimate_corrections"

    if (row["total_tickets"] >= 20 and row["total_ops"] >= 30
            and row["refund_cnt"] <= 3 and row["seat_blocking_score"] < 50):
        return "tourist_group_pattern"

    if (row["fio_fake_score_max"] >= 3 and row["fio_fake_score_max"] <= 5
            and row["total_tickets"] <= 5 and row["refund_cnt"] <= 1):
        return "foreign_name_pattern"

    if (row["refund_cnt"] >= 3 and row["refund_cnt"] <= 4
            and row.get("suspicious_refund_pattern_cnt", 0) == 0
            and row["seat_blocking_score"] < 50):
        return "single_refund_signal"

    if (row.get("night_share", 0) >= 0.3 and row["total_tickets"] < 10
            and row["refund_cnt"] <= 2):
        return "legitimate_night_activity"

    return None


def requires_corroboration(signal: str) -> bool:
    """Check if a signal requires additional corroboration to be actionable.

    Returns True if this signal alone is not enough for HIGH/CRITICAL risk.
    """
    no_corr_needed = {
        "seat_blocking_extreme",
        "extreme_refund_abuse",
        "organized_fraud_pattern",
        "multi_signal_alignment",
    }
    return signal not in no_corr_needed


def count_independent_signals(row: pd.Series) -> int:
    """
    Count independent fraud signals (not double-counting same underlying issue).

    Returns count of distinct fraud categories present.
    """
    signals = 0

    # 1. Identity issue. Counts as one signal, but never enough by itself.
    if (
        row.get("fio_fake_score_max", 0) >= 8
        or row.get("consistency_risk_score", 0) >= 20
        or (
            row.get("missing_identity_flag", False)
            and (row.get("refund_cnt", 0) >= 3 or row.get("total_tickets", 0) >= 10)
        )
    ):
        signals += 1

    # 2. Refund abuse. A couple of ordinary refunds is not a fraud signal.
    if (
        row.get("refund_cnt", 0) >= 5
        or row.get("suspicious_refund_pattern_cnt", 0) >= 3
        or (
            row.get("refund_cnt", 0) >= 3
            and row.get("refund_share", 0) >= 0.5
        )
    ):
        signals += 1

    # 3. Seat blocking
    if row.get("seat_blocking_score", 0) >= 50:
        signals += 1

    # 4. Rapid/technical cancellations
    if (row.get("rapid_cancel_cnt", 0) >= 2
            or row.get("technical_cancel_cnt", 0) >= 2):
        signals += 1

    # 5. Close timing + refund
    if (row.get("close_refund_cnt", 0) >= 2
            and row.get("refund_close_ratio", 0) >= 0.3):
        signals += 1

    # 6. Concentrated/high-volume behavior. This is separate from refunds.
    if (
        row.get("max_tickets_same_depday", 0) >= 10
        or row.get("tickets_per_train_peak", 0) >= 6
        or row.get("total_tickets", 0) >= 30
    ):
        signals += 1

    # 7. Operational footprint: many terminals/cashdesks suggests organized
    # usage only when the passenger has enough activity.
    if (
        row.get("terminal_count", 0) >= 8
        and row.get("total_ops", row.get("total_tickets", 0)) >= 20
    ):
        signals += 1

    return signals


def has_core_fraud_evidence(row: pd.Series) -> bool:
    """Return True when there is actionable behavior, not only data quality.

    Core evidence is required for HIGH/CRITICAL. This prevents cases like
    "suspicious name only" or "large legitimate group booking" from being
    presented as fraud.
    """
    return bool(
        row.get("seat_blocking_score", 0) >= 50
        or row.get("refund_cnt", 0) >= 5
        or row.get("suspicious_refund_pattern_cnt", 0) >= 3
        or row.get("rapid_cancel_cnt", 0) >= 2
        or row.get("technical_cancel_cnt", 0) >= 2
        or (
            row.get("close_refund_cnt", 0) >= 2
            and row.get("refund_close_ratio", 0) >= 0.3
        )
        or row.get("consistency_risk_score", 0) >= 40
        or (
            row.get("terminal_count", 0) >= 8
            and (
                row.get("refund_cnt", 0) >= 3
                or row.get("total_tickets", 0) >= 30
            )
        )
    )
