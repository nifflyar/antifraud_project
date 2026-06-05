"""Structured reasoning and explanation generation for fraud scores."""

from typing import List, Dict, Any
import pandas as pd


def build_top_reasons(row: pd.Series, max_reasons: int = 5) -> List[Dict[str, Any]]:
    """
    Build structured, human-readable reasons for a passenger's risk score.

    Args:
        row: DataFrame row with all feature/score columns
        max_reasons: Maximum number of reasons to return

    Returns:
        List of reason dicts with code, text, severity, value, component
    """
    reasons: List[Dict[str, Any]] = []

    refund_cnt = int(row.get("refund_cnt", 0))
    refund_share = float(row.get("refund_share", 0))
    paid_refund_share = float(row.get("paid_refund_share", 0))
    refund_close_ratio = float(row.get("refund_close_ratio", 0))
    close_refund_cnt = int(row.get("close_refund_cnt", 0))
    max_same_depday = int(row.get("max_tickets_same_depday", 0))
    max_same_train = int(row.get("tickets_per_train_peak", 0))
    fake_fio_score = float(row.get("fio_fake_score_max", 0))
    night_share = float(row.get("night_share", 0))
    total_tickets = int(row.get("total_tickets", 0))
    rapid_cancel_cnt = int(row.get("rapid_cancel_cnt", 0))
    seat_blocking_score = float(row.get("seat_blocking_score", 0))
    terminal_count = int(row.get("terminal_count", 0))
    consistency_issues = row.get("consistency_issues", [])
    suspicious_refund_pattern_cnt = int(row.get("suspicious_refund_pattern_cnt", 0))
    identity_has_corroboration = (
        refund_cnt >= 3
        or suspicious_refund_pattern_cnt >= 3
        or total_tickets >= 20
        or max_same_depday >= 10
        or max_same_train >= 6
        or terminal_count >= 5
        or seat_blocking_score >= 50
        or float(row.get("consistency_risk_score", 0)) >= 20
    )

    # 1. Refund patterns
    if refund_cnt >= 5:
        reasons.append(
            {
                "code": "MANY_REFUNDS",
                "text": f"{refund_cnt} refunds",
                "severity": "HIGH",
                "value": refund_cnt,
                "component": "refund_score",
                "confidence": 0.85,
            }
        )
    elif refund_cnt >= 3:
        reasons.append(
            {
                "code": "SEVERAL_REFUNDS",
                "text": f"{refund_cnt} refunds",
                "severity": "MEDIUM",
                "value": refund_cnt,
                "component": "refund_score",
                "confidence": 0.75,
            }
        )

    # 2. High refund share
    if refund_share >= 0.50:
        reasons.append(
            {
                "code": "HIGH_REFUND_SHARE",
                "text": f"{refund_share:.0%} refund share",
                "severity": "HIGH",
                "value": refund_share,
                "component": "refund_score",
                "confidence": 0.90,
            }
        )
    elif refund_share >= 0.30:
        reasons.append(
            {
                "code": "ELEVATED_REFUND_SHARE",
                "text": f"{refund_share:.0%} refund share",
                "severity": "MEDIUM",
                "value": refund_share,
                "component": "refund_score",
                "confidence": 0.80,
            }
        )

    # 3. Close to departure refunds
    if close_refund_cnt >= 2 and refund_close_ratio >= 0.50:
        reasons.append(
            {
                "code": "REFUNDS_CLOSE_TO_DEPARTURE",
                "text": f"{close_refund_cnt} refunds within 24h of departure ({refund_close_ratio:.0%})",
                "severity": "CRITICAL",
                "value": refund_close_ratio,
                "component": "timing_score",
                "confidence": 0.95,
            }
        )
    elif close_refund_cnt >= 1 and refund_close_ratio >= 0.30:
        reasons.append(
            {
                "code": "SOME_REFUNDS_CLOSE_TO_DEPARTURE",
                "text": f"refunds within 24h of departure ({refund_close_ratio:.0%})",
                "severity": "HIGH",
                "value": refund_close_ratio,
                "component": "timing_score",
                "confidence": 0.85,
            }
        )

    # 4. Seat clustering
    if max_same_train >= 6:
        reasons.append(
            {
                "code": "SEAT_CLUSTERING",
                "text": f"{max_same_train} tickets for same train and departure",
                "severity": "HIGH",
                "value": max_same_train,
                "component": "seat_blocking_score",
                "confidence": 0.80,
            }
        )
    elif max_same_train >= 4:
        reasons.append(
            {
                "code": "MULTIPLE_TICKETS_SAME_TRAIN",
                "text": f"{max_same_train} tickets for same train and departure",
                "severity": "MEDIUM",
                "value": max_same_train,
                "component": "seat_blocking_score",
                "confidence": 0.70,
            }
        )

    if max_same_depday >= 8:
        reasons.append(
            {
                "code": "MANY_TICKETS_SAME_DAY",
                "text": f"{max_same_depday} tickets for same departure day",
                "severity": "HIGH",
                "value": max_same_depday,
                "component": "volume_score",
                "confidence": 0.75,
            }
        )
    elif max_same_depday >= 5:
        reasons.append(
            {
                "code": "SEVERAL_TICKETS_SAME_DAY",
                "text": f"{max_same_depday} tickets for same departure day",
                "severity": "MEDIUM",
                "value": max_same_depday,
                "component": "volume_score",
                "confidence": 0.65,
            }
        )

    # 5. Fake FIO
    if fake_fio_score >= 8:
        reasons.append(
            {
                "code": "FAKE_OR_PLACEHOLDER_FIO",
                "text": (
                    f"FIO pattern appears fake (score {fake_fio_score:.0f}/10)"
                    if identity_has_corroboration
                    else f"FIO pattern appears fake but has no behavioral corroboration (score {fake_fio_score:.0f}/10)"
                ),
                "severity": "HIGH" if identity_has_corroboration else "MEDIUM",
                "value": fake_fio_score,
                "component": "identity_score",
                "confidence": 0.85 if identity_has_corroboration else 0.60,
            }
        )
    elif fake_fio_score >= 5:
        reasons.append(
            {
                "code": "SUSPICIOUS_FIO",
                "text": f"unusual FIO pattern (score {fake_fio_score:.0f}/10)",
                "severity": "MEDIUM",
                "value": fake_fio_score,
                "component": "identity_score",
                "confidence": 0.70,
            }
        )

    # 6. Night activity
    if night_share >= 0.50 and total_tickets >= 5:
        reasons.append(
            {
                "code": "NIGHT_ACTIVITY",
                "text": f"{night_share:.0%} night operations (unusual pattern)",
                "severity": "MEDIUM",
                "value": night_share,
                "component": "timing_score",
                "confidence": 0.60,
            }
        )

    # 7. Rapid cancellations
    if rapid_cancel_cnt >= 2:
        reasons.append(
            {
                "code": "RAPID_CANCELLATIONS",
                "text": f"{rapid_cancel_cnt} tickets cancelled within 10 minutes",
                "severity": "HIGH",
                "value": rapid_cancel_cnt,
                "component": "seat_blocking_score",
                "confidence": 0.75,
            }
        )

    # 8. Seat blocking
    if seat_blocking_score >= 80:
        reasons.append(
            {
                "code": "SEAT_BLOCKING_DETECTED",
                "text": "Strong seat-blocking pattern detected",
                "severity": "CRITICAL",
                "value": seat_blocking_score,
                "component": "seat_blocking_score",
                "confidence": 0.90,
            }
        )

    # 9. Identity consistency issues
    if isinstance(consistency_issues, list) and consistency_issues:
        issue_text = consistency_issues[0]
        if "same_iin_multiple_fio" in issue_text:
            reasons.append(
                {
                    "code": "IDENTITY_MISMATCH",
                    "text": issue_text,
                    "severity": "HIGH",
                    "value": 1,
                    "component": "identity_score",
                    "confidence": 0.80,
                }
            )

    # 10. Terminal concentration
    if terminal_count >= 5:
        terminal_severity = "HIGH" if terminal_count >= 10 and total_tickets >= 30 else "LOW"
        reasons.append(
            {
                "code": "MULTIPLE_TERMINALS",
                "text": f"operations across {terminal_count} different terminals",
                "severity": terminal_severity,
                "value": terminal_count,
                "component": "concentration_score",
                "confidence": 0.75 if terminal_severity == "HIGH" else 0.50,
            }
        )

    # Sort by severity (CRITICAL > HIGH > MEDIUM > LOW) and confidence
    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    reasons.sort(
        key=lambda x: (
            -severity_order.get(x.get("severity", "LOW"), 0),
            -x.get("confidence", 0),
        )
    )

    return reasons[:max_reasons]
