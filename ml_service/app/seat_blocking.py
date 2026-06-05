"""Intelligent seat-blocking detection with false-positive control."""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


def detect_seat_blocking(transactions_df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Detect seat-blocking behavior with nuanced scoring and false-positive control.

    Seat-blocking patterns:
    1. Multiple tickets for same train + departure created then refunded/cancelled
    2. Refunds/cancellations close to departure time
    3. Pattern repeated across multiple trains
    4. Same terminal/cashdesk concentration

    Args:
        transactions_df: DataFrame with:
        - passenger_id, train_no, dep_datetime, op_datetime, op_type
        - terminal, channel, amount

    Returns:
        Dict[passenger_id] -> {
            'seat_blocking_score': int (0-100),
            'seat_blocking_flag': bool (CRITICAL level detected),
            'block_signals': int (count of strong signals detected),
            'cluster_metrics': {
                'largest_cluster_size': int,
                'largest_cluster_refunds': int,
                'avg_minutes_to_departure': float,
                'close_refund_ratio': float,
            }
            'issues': list of strings
        }
    """

    df = transactions_df.copy()

    # Ensure datetime columns are parsed
    df["op_datetime"] = pd.to_datetime(df["op_datetime"], errors="coerce")
    df["dep_datetime"] = pd.to_datetime(df["dep_datetime"], errors="coerce")

    # Skip rows with missing datetime
    df = df.dropna(subset=["dep_datetime"])

    df["is_sale"] = df["op_type"].eq("sale")
    df["is_refund"] = df["op_type"].eq("refund")
    df["minutes_to_dep"] = (df["dep_datetime"] - df["op_datetime"]).dt.total_seconds() / 60
    df["refund_minutes_to_dep"] = np.where(df["is_refund"], df["minutes_to_dep"], np.nan)
    df["is_close_refund"] = df["is_refund"] & df["minutes_to_dep"].between(0, 24 * 60)
    df["is_very_close_refund"] = df["is_refund"] & df["minutes_to_dep"].between(0, 60)

    cluster_cols = ["passenger_id", "train_no", "dep_datetime"]
    clusters = (
        df.groupby(cluster_cols, dropna=False)
        .agg(
            cluster_size=("op_type", "size"),
            confirmed_count=("is_sale", "sum"),
            refunded_count=("is_refund", "sum"),
            close_refunds=("is_close_refund", "sum"),
            very_close_refunds=("is_very_close_refund", "sum"),
            avg_minutes_to_dep=("refund_minutes_to_dep", "mean"),
        )
        .reset_index()
    )
    if clusters.empty:
        return {}

    largest = (
        clusters.sort_values(["passenger_id", "cluster_size"], ascending=[True, False])
        .drop_duplicates("passenger_id")
        .copy()
    )
    passenger_stats = (
        df.groupby("passenger_id", dropna=False)
        .agg(
            unique_trains=("train_no", "nunique"),
            unique_deps=("dep_datetime", "nunique"),
        )
        .reset_index()
    )
    largest = largest.merge(passenger_stats, on="passenger_id", how="left")
    largest["close_refund_ratio"] = np.where(
        largest["refunded_count"] > 0,
        largest["close_refunds"] / largest["refunded_count"],
        0.0,
    )

    cluster_size = largest["cluster_size"]
    volume_score = np.select(
        [cluster_size >= 10, cluster_size >= 7, cluster_size >= 5, cluster_size >= 3],
        [25, 20, 15, 10],
        default=(cluster_size * 2).clip(lower=0),
    )

    avg_minutes = largest["avg_minutes_to_dep"]
    close_ratio = largest["close_refund_ratio"]
    timing_score = np.select(
        [
            largest["very_close_refunds"] >= 1,
            close_ratio >= 0.60,
            close_ratio >= 0.30,
            avg_minutes.between(0, 24 * 60),
        ],
        [30, 25, 15, 10],
        default=0,
    )

    refunded_count = largest["refunded_count"]
    lifecycle_score = np.select(
        [refunded_count >= 4, refunded_count >= 3, refunded_count >= 2],
        [25, 18, 10],
        default=0,
    )

    repeated_strong = (largest["unique_trains"] >= 5) | (largest["unique_deps"] >= 5)
    repeated_some = (largest["unique_trains"] >= 3) | (largest["unique_deps"] >= 3)
    repetition_score = np.select([repeated_strong, repeated_some], [20, 12], default=0)

    score = (
        pd.Series(volume_score, index=largest.index)
        + pd.Series(timing_score, index=largest.index)
        + pd.Series(lifecycle_score, index=largest.index)
        + pd.Series(repetition_score, index=largest.index)
    ).astype(float)

    signals = repeated_some.astype(int)
    signals += (
        (largest["cluster_size"] >= 5)
        & (largest["refunded_count"] >= 3)
        & ((close_ratio >= 0.30) | (largest["very_close_refunds"] >= 1))
    ).astype(int)
    signals += ((close_ratio >= 0.60) & (largest["confirmed_count"] >= 1)).astype(int)
    signals += ((largest["confirmed_count"] >= 1) & (largest["refunded_count"] >= 2)).astype(int)

    no_close = close_ratio.eq(0)
    score = np.where(no_close, np.minimum(score, 65), score)
    far_from_departure = avg_minutes.gt(72 * 60).fillna(False)
    score = np.where(far_from_departure, np.maximum(0, score - 20), score)
    score = pd.Series(score, index=largest.index).clip(0, 100)
    is_critical = (signals >= 2) & (score >= 70)

    blocking_data: Dict[str, Dict] = {}
    for idx, row in largest.iterrows():
        issues: List[str] = []
        if row["very_close_refunds"] >= 1:
            issues.append("very_close_refund:<1h")
        elif row["close_refund_ratio"] >= 0.60:
            issues.append(f"high_close_refund_ratio:{row['close_refund_ratio']:.0%}")
        elif row["close_refund_ratio"] >= 0.30:
            issues.append(f"some_close_refunds:{row['close_refund_ratio']:.0%}")
        elif pd.notna(row["avg_minutes_to_dep"]) and row["avg_minutes_to_dep"] <= 24 * 60:
            issues.append("refund_within_24h_avg")

        if row["refunded_count"] >= 4:
            issues.append(f"many_refunds:{int(row['refunded_count'])}")
        elif row["refunded_count"] >= 3:
            issues.append(f"several_refunds:{int(row['refunded_count'])}")
        elif row["refunded_count"] >= 2:
            issues.append(f"multiple_refunds:{int(row['refunded_count'])}")

        if row["unique_trains"] >= 5 or row["unique_deps"] >= 5:
            issues.append(f"repeated_pattern:{int(row['unique_trains'])}trains")
        if (
            row["cluster_size"] >= 5
            and row["refunded_count"] >= 3
            and (row["close_refund_ratio"] >= 0.30 or row["very_close_refunds"] >= 1)
        ):
            issues.append("signal:strong_cluster_with_timing")
        if row["close_refund_ratio"] == 0:
            issues.append("fp_control:no_close_refunds")
        if pd.notna(row["avg_minutes_to_dep"]) and row["avg_minutes_to_dep"] > 72 * 60:
            issues.append("fp_control:far_from_departure")

        avg_value = row["avg_minutes_to_dep"]
        blocking_data[str(row["passenger_id"])] = {
            "seat_blocking_score": int(score.loc[idx]),
            "seat_blocking_flag": bool(is_critical.loc[idx]),
            "block_signals": int(signals.loc[idx]),
            "cluster_metrics": {
                "largest_cluster_size": int(row["cluster_size"]),
                "largest_cluster_refunds": int(row["refunded_count"]),
                "largest_cluster_confirmed": int(row["confirmed_count"]),
                "avg_minutes_to_departure": float(avg_value) if pd.notna(avg_value) else None,
                "close_refund_ratio": float(row["close_refund_ratio"]),
                "unique_trains": int(row["unique_trains"]),
                "unique_dep_days": int(row["unique_deps"]),
            },
            "issues": issues[:4],
        }

    return blocking_data


def _empty_blocking_data() -> Dict:
    """Return empty/default blocking data."""
    return {
        "seat_blocking_score": 0,
        "seat_blocking_flag": False,
        "block_signals": 0,
        "cluster_metrics": {
            "largest_cluster_size": 0,
            "largest_cluster_refunds": 0,
            "largest_cluster_confirmed": 0,
            "avg_minutes_to_departure": None,
            "close_refund_ratio": 0.0,
            "unique_trains": 0,
            "unique_dep_days": 0,
        },
        "issues": [],
    }
