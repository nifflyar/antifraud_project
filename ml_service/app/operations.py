"""Operation-level risk scoring."""

from typing import Dict, List
import pandas as pd
import numpy as np


def score_operations(
    transactions_df: pd.DataFrame,
    passenger_scores: pd.DataFrame,
    concentration_data: Dict[str, Dict] | None = None,
) -> pd.DataFrame:
    """
    Assign risk scores to individual operations (transactions).

    Args:
        transactions_df: DataFrame with transaction details
        passenger_scores: DataFrame with passenger-level scores
        concentration_data: Optional dict of concentration metrics by dimension

    Returns:
        DataFrame with operation_risk_score, operation_risk_band columns added
    """
    if transactions_df.empty:
        return transactions_df.copy()

    df = transactions_df.copy()

    # Merge passenger scores
    df = df.merge(
        passenger_scores[["passenger_id", "final_score", "risk_band", "seat_blocking_flag"]],
        on="passenger_id",
        how="left",
        suffixes=("", "_passenger"),
    )

    # Calculate minutes to departure
    df["op_datetime"] = pd.to_datetime(df["op_datetime"], errors="coerce")
    df["dep_datetime"] = pd.to_datetime(df["dep_datetime"], errors="coerce")
    df["minutes_to_dep"] = (df["dep_datetime"] - df["op_datetime"]).dt.total_seconds() / 60

    operation_scores = []

    for _, row in df.iterrows():
        score = 0
        issues = []

        # Base factors
        is_refund = row.get("op_type") == "refund"
        minutes_to_dep = row.get("minutes_to_dep")

        # 1. Operation type (refund/cancel is riskier)
        if is_refund:
            score += 20
            issues.append("refund_operation")

        # 2. Passenger risk level
        passenger_score = row.get("final_score", 0)
        if passenger_score >= 80:
            score += 30
            issues.append("high_risk_passenger")
        elif passenger_score >= 60:
            score += 20
            issues.append("medium_risk_passenger")
        elif passenger_score >= 40:
            score += 10

        # 3. Timing to departure
        if minutes_to_dep is not None and minutes_to_dep >= 0:
            if minutes_to_dep <= 60:  # Within 1 hour
                score += 40
                issues.append("critical_timing_<1h")
            elif minutes_to_dep <= 6 * 60:  # Within 6 hours
                score += 30
                issues.append("very_close_timing_<6h")
            elif minutes_to_dep <= 24 * 60:  # Within 24 hours
                score += 20
                issues.append("close_timing_<24h")
            elif minutes_to_dep <= 72 * 60:  # Within 72 hours
                score += 10

        # 4. Terminal/channel risk
        if concentration_data:
            terminal = row.get("terminal")
            channel = row.get("channel")

            if terminal and terminal in concentration_data.get("terminal", {}):
                term_lift = concentration_data["terminal"][terminal].get("lift_vs_base", 1)
                if term_lift > 3:
                    score += 20
                    issues.append(f"very_risky_terminal:{term_lift:.1f}x")
                elif term_lift > 2:
                    score += 12
                    issues.append(f"risky_terminal:{term_lift:.1f}x")

            if channel and channel in concentration_data.get("channel", {}):
                chan_lift = concentration_data["channel"][channel].get("lift_vs_base", 1)
                if chan_lift > 3:
                    score += 15
                    issues.append(f"very_risky_channel:{chan_lift:.1f}x")

        # 5. Seat blocking flag
        is_seat_blocking = row.get("seat_blocking_flag", False)
        if is_seat_blocking:
            score += 20
            issues.append("part_of_seat_blocking")

        # 6. Amount anomaly (high value refunds are suspicious)
        amount = row.get("amount")
        if is_refund and amount and amount > 50000:  # High value
            score += 15
            issues.append("high_value_refund")

        # Cap and normalize
        operation_score = min(100, max(0, score))

        operation_scores.append(
            {
                "id": row.get("id"),
                "operation_risk_score": int(operation_score),
                "operation_issues": ",".join(issues[:3]),
            }
        )

    result_df = pd.DataFrame(operation_scores)
    if not result_df.empty:
        result_df["operation_risk_band"] = result_df["operation_risk_score"].apply(
            _operation_risk_band
        )
        df = df.merge(
            result_df[["id", "operation_risk_score", "operation_risk_band", "operation_issues"]],
            on="id",
            how="left",
        )
    else:
        df["operation_risk_score"] = 0
        df["operation_risk_band"] = "LOW"
        df["operation_issues"] = ""

    return df


def _operation_risk_band(score: int) -> str:
    """Convert operation risk score to band."""
    if score >= 85:
        return "CRITICAL"
    elif score >= 65:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"
