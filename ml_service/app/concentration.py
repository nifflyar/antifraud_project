"""Enhanced risk concentration analysis by dimension."""

from typing import Dict, List
import pandas as pd
import numpy as np


def calculate_risk_concentration(
    transactions_df: pd.DataFrame,
    passenger_scores: pd.DataFrame,
    min_total_ops: int = 10,
    smoothing_alpha: float = 2.0,
) -> List[Dict]:
    """
    Calculate risk concentration metrics by dimension.

    Dimensions: channel, aggregator, terminal, cashdesk, point_of_sale

    Args:
        transactions_df: Transaction data
        passenger_scores: Passenger risk scores
        min_total_ops: Minimum operations to include dimension in ranking
        smoothing_alpha: Bayesian smoothing parameter

    Returns:
        List of concentration records with metrics
    """
    if transactions_df.empty or passenger_scores.empty:
        return []

    df = transactions_df.copy()

    # Merge passenger scores
    df = df.merge(
        passenger_scores[["passenger_id", "final_score", "risk_band"]],
        on="passenger_id",
        how="left",
    )

    # Mark high/critical risk operations
    df["is_highrisk_op"] = df["risk_band"].isin(["HIGH", "CRITICAL"])
    df["is_critical_op"] = df["risk_band"] == "CRITICAL"

    # Calculate base rate
    base_highrisk_share = float(df["is_highrisk_op"].mean()) if len(df) > 0 else 0.0

    concentration_records: List[Dict] = []
    dimensions = {
        "channel": "channel",
        "aggregator": "aggregator",
        "terminal": "terminal",
        "cashdesk": "cashdesk",
        "point_of_sale": "point_of_sale",
    }

    for dim_type, col in dimensions.items():
        if col not in df.columns:
            continue

        # Group by dimension
        grouped = (
            df.dropna(subset=[col])
            .groupby(col)
            .agg(
                total_ops=("id", "count"),
                highrisk_ops=("is_highrisk_op", "sum"),
                critical_ops=("is_critical_op", "sum"),
                total_amount=("amount", "sum"),
                suspicious_amount=("amount", lambda x: x[df.loc[x.index, "is_highrisk_op"]].sum()),
            )
            .reset_index()
        )

        # Filter by minimum operations
        grouped = grouped[grouped["total_ops"] >= min_total_ops]

        # Calculate metrics with smoothing
        grouped["share_highrisk_ops"] = (
            grouped["highrisk_ops"] / grouped["total_ops"]
        ).astype(float)
        grouped["share_critical_ops"] = (
            grouped["critical_ops"] / grouped["total_ops"]
        ).astype(float)

        # Bayesian smoothing to avoid over-ranking low-count dimensions
        grouped["share_highrisk_ops_smoothed"] = (
            grouped["highrisk_ops"] + smoothing_alpha
        ) / (grouped["total_ops"] + smoothing_alpha * 2)

        # Lift vs baseline
        grouped["lift_vs_base"] = np.where(
            base_highrisk_share > 0,
            grouped["share_highrisk_ops_smoothed"] / base_highrisk_share,
            1.0,
        )

        # Sort by lift descending
        grouped = grouped.sort_values("lift_vs_base", ascending=False)

        for _, row in grouped.iterrows():
            concentration_records.append(
                {
                    "dimension_type": dim_type,
                    "dimension_value": str(row[col])[:255],
                    "total_ops": int(row["total_ops"]),
                    "highrisk_ops": int(row["highrisk_ops"]),
                    "critical_ops": int(row["critical_ops"]),
                    "share_highrisk_ops": float(row["share_highrisk_ops"]),
                    "share_critical_ops": float(row["share_critical_ops"]),
                    "lift_vs_base": float(row["lift_vs_base"]),
                    "base_highrisk_share": base_highrisk_share,
                    "total_amount": float(row["total_amount"]) if row["total_amount"] else 0.0,
                    "suspicious_amount": float(row["suspicious_amount"])
                    if row["suspicious_amount"]
                    else 0.0,
                }
            )

    return concentration_records
