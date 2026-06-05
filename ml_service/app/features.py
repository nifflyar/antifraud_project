"""Enhanced feature engineering for passenger risk scoring."""

import pandas as pd
import numpy as np
from datetime import timedelta


def build_enhanced_features(df: pd.DataFrame, upload_id: int | None) -> pd.DataFrame:
    """
    Build comprehensive risk features from transactions.

    Args:
        df: Clean transactions DataFrame
        upload_id: Upload ID for tracking

    Returns:
        DataFrame with passenger_id and all feature columns
    """
    if df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Ensure datetime columns are parsed
    for col in ["op_datetime", "dep_datetime"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Mark operation types
    df["is_sale"] = df["op_type"].eq("sale")
    df["is_refund"] = df["op_type"].eq("refund")
    df["ticket_no"] = df["ticket_no"].fillna("").astype(str)

    # Time features
    df["op_hour"] = df["op_datetime"].dt.hour.fillna(-1)
    df["is_night"] = df["op_hour"].between(0, 5)
    df["op_month"] = df["op_datetime"].dt.to_period("M").astype(str)
    df["dep_day"] = df["dep_datetime"].dt.date.astype(str)
    df["op_date"] = df["op_datetime"].dt.date.astype(str)

    # Minutes to departure (pre-compute for performance)
    df["minutes_to_dep"] = (df["dep_datetime"] - df["op_datetime"]).dt.total_seconds() / 60

    # Refund timing
    df["is_close_refund"] = (
        df["is_refund"] & df["minutes_to_dep"].between(0, 24 * 60)
    )  # Within 24h
    df["is_very_close_refund"] = (
        df["is_refund"] & df["minutes_to_dep"].between(0, 60)
    )  # Within 1h

    # Same-minute operations (technical cancellations)
    df["same_minute_key"] = (
        df["passenger_id"].astype(str)
        + "|"
        + df["op_datetime"].dt.floor("T").astype(str)
    )

    # Detect suspicious refund patterns (multiple similar refunds per day)
    suspicious_refunds = _detect_suspicious_refund_patterns(df)

    # Aggregate by passenger
    g = df.groupby("passenger_id", dropna=False)

    # Ensure fio_fake_score exists, default to 0 if missing
    if "fio_fake_score" not in df.columns:
        df["fio_fake_score"] = 0

    features = g.agg(
        total_ops=("id", "count"),
        total_tickets=("ticket_no", lambda x: pd.Series.nunique(x)),
        sale_cnt=("is_sale", "sum"),
        paid_cnt=("is_sale", "sum"),  # Assuming all sales are paid
        refund_cnt=("is_refund", "sum"),
        night_tickets=("is_night", "sum"),
        fio_fake_score_max=("fio_fake_score", "max"),
        terminal_count=("terminal", lambda x: pd.Series.nunique(x)),
        cashdesk_count=("cashdesk", lambda x: pd.Series.nunique(x)),
        channel_count=("channel", lambda x: pd.Series.nunique(x)),
        aggregator_count=("aggregator", lambda x: pd.Series.nunique(x)),
        amount_sum=("amount", "sum"),
        close_refund_cnt=("is_close_refund", "sum"),
        very_close_refund_cnt=("is_very_close_refund", "sum"),
    ).reset_index()

    # Calculate shares
    denom = features["sale_cnt"] + features["refund_cnt"]
    features["refund_share"] = np.where(denom > 0, features["refund_cnt"] / denom, 0)

    # Paid refund share (refunds / paid sales)
    features["paid_refund_share"] = np.where(
        features["paid_cnt"] > 0, features["refund_cnt"] / features["paid_cnt"], 0
    )

    features["night_share"] = np.where(
        features["total_ops"] > 0, features["night_tickets"] / features["total_ops"], 0
    )

    features["refund_close_ratio"] = np.where(
        features["refund_cnt"] > 0,
        features["close_refund_cnt"] / features["refund_cnt"],
        0,
    )

    # Amount refunded
    refunds_df = df[df["is_refund"]].copy()
    amount_refunded = (
        refunds_df.groupby("passenger_id")["amount"].sum().reset_index(
            name="amount_refunded"
        )
    )
    features = features.merge(amount_refunded, on="passenger_id", how="left")
    features["amount_refunded"] = features["amount_refunded"].fillna(0)

    # Rapid cancellations (refund within 10 minutes of corresponding sale)
    rapid_cancels = _detect_rapid_cancels(df)
    features = features.merge(rapid_cancels, on="passenger_id", how="left")
    features["rapid_cancel_cnt"] = features["rapid_cancel_cnt"].fillna(0)

    # Suspicious refund patterns (multiple similar refunds per day)
    features = features.merge(suspicious_refunds, on="passenger_id", how="left")
    features["suspicious_refund_pattern_cnt"] = features["suspicious_refund_pattern_cnt"].fillna(0)
    features["refund_amount_diversity"] = features["refund_amount_diversity"].fillna(1.0)

    # Technical cancellations (same minute operations)
    technical_cancels = _detect_technical_cancels(df)
    features = features.merge(technical_cancels, on="passenger_id", how="left")
    features["technical_cancel_cnt"] = features["technical_cancel_cnt"].fillna(0)

    # Max tickets by grouping
    sales = df[df["is_sale"]].copy()

    max_month = _max_group_count(sales, ["passenger_id", "op_month"], "max_tickets_month")
    max_depday = _max_group_count(
        sales, ["passenger_id", "dep_day"], "max_tickets_same_depday"
    )

    train_dep_key = sales["train_no"].fillna("unknown").astype(str) + "|" + sales["dep_datetime"].astype(str)
    train_peak_df = sales.copy()
    train_peak_df["train_dep_key"] = train_dep_key
    train_peak = _max_group_count(
        train_peak_df,
        ["passenger_id", "train_dep_key"],
        "tickets_per_train_peak",
    )

    for add in [max_month, max_depday, train_peak]:
        features = features.merge(add, on="passenger_id", how="left")

    for col in [
        "max_tickets_month",
        "max_tickets_same_depday",
        "tickets_per_train_peak",
    ]:
        features[col] = features[col].fillna(0)

    # Average minutes to departure for refunds
    refund_times = (
        refunds_df.groupby("passenger_id")["minutes_to_dep"]
        .mean()
        .reset_index(name="avg_minutes_to_departure_for_refunds")
    )
    features = features.merge(refund_times, on="passenger_id", how="left")

    features["upload_id"] = upload_id

    return features


def _max_group_count(
    frame: pd.DataFrame, group_cols: list[str], name: str
) -> pd.DataFrame:
    """Get max unique ticket count per group."""
    if frame.empty:
        return pd.DataFrame(columns=["passenger_id", name])

    tmp = (
        frame.groupby(group_cols)["ticket_no"]
        .nunique()
        .reset_index(name="cnt")
    )
    return tmp.groupby("passenger_id")["cnt"].max().reset_index(name=name)


def _detect_rapid_cancels(df: pd.DataFrame) -> pd.DataFrame:
    """Detect refunds that happen within 10 minutes of ticket sale."""
    sales = df.loc[
        df["is_sale"],
        ["passenger_id", "ticket_no", "op_datetime"],
    ].rename(columns={"op_datetime": "sale_time"})
    refunds = df.loc[
        df["is_refund"],
        ["passenger_id", "ticket_no", "op_datetime"],
    ].rename(columns={"op_datetime": "refund_time"})

    if sales.empty or refunds.empty:
        return pd.DataFrame(columns=["passenger_id", "rapid_cancel_cnt"])

    matched = refunds.merge(sales, on=["passenger_id", "ticket_no"], how="inner")
    if matched.empty:
        return pd.DataFrame(columns=["passenger_id", "rapid_cancel_cnt"])

    delta_minutes = (matched["refund_time"] - matched["sale_time"]).dt.total_seconds() / 60
    rapid = matched.loc[delta_minutes.between(0, 10, inclusive="neither")]
    if rapid.empty:
        return pd.DataFrame(columns=["passenger_id", "rapid_cancel_cnt"])

    return (
        rapid.groupby("passenger_id")
        .size()
        .reset_index(name="rapid_cancel_cnt")
    )


def _detect_technical_cancels(df: pd.DataFrame) -> pd.DataFrame:
    """Detect same-minute оформление->гашение without payment confirmation."""
    df_temp = df.copy()
    df_temp["op_minute"] = df_temp["op_datetime"].dt.floor("T")

    grouped = (
        df_temp.dropna(subset=["passenger_id", "op_minute"])
        .groupby(["passenger_id", "op_minute"], dropna=False)
        .agg(
            has_sale=("is_sale", "any"),
            has_refund=("is_refund", "any"),
            refund_count=("is_refund", "sum"),
        )
        .reset_index()
    )
    if grouped.empty:
        return pd.DataFrame(columns=["passenger_id", "technical_cancel_cnt"])

    technical = grouped[grouped["has_sale"] & grouped["has_refund"]]
    if technical.empty:
        return pd.DataFrame(columns=["passenger_id", "technical_cancel_cnt"])

    return (
        technical.groupby("passenger_id")["refund_count"]
        .sum()
        .reset_index(name="technical_cancel_cnt")
    )


def _detect_suspicious_refund_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect suspicious patterns:
    - Multiple similar-amount refunds on same day
    - High diversity in refund amounts (different prices for same route)
    - Rapid refund clustering (multiple refunds in 1-hour window on same day)

    Returns:
        DataFrame with suspicious_refund_pattern_cnt and refund_amount_diversity
    """
    refunds = df[df["op_type"] == "refund"].copy()

    if refunds.empty:
        return pd.DataFrame(columns=["passenger_id", "suspicious_refund_pattern_cnt", "refund_amount_diversity"])

    refunds = refunds.dropna(subset=["passenger_id", "op_datetime"]).copy()
    if refunds.empty:
        return pd.DataFrame(columns=["passenger_id", "suspicious_refund_pattern_cnt", "refund_amount_diversity"])

    refunds["op_date"] = refunds["op_datetime"].dt.date
    keys = ["passenger_id", "op_date"]

    amount_sorted = refunds.sort_values(keys + ["amount"])
    prev_amount = amount_sorted.groupby(keys)["amount"].shift()
    similar_amount = (
        prev_amount.gt(0)
        & amount_sorted["amount"].notna()
        & ((amount_sorted["amount"] - prev_amount).abs() / prev_amount).le(0.05)
    )
    similar_counts = (
        similar_amount.groupby(amount_sorted["passenger_id"])
        .sum()
        .rename("similar_amount_cnt")
    )

    time_sorted = refunds.sort_values(keys + ["op_datetime"])
    prev_time = time_sorted.groupby(keys)["op_datetime"].shift()
    close_time = (
        prev_time.notna()
        & ((time_sorted["op_datetime"] - prev_time).dt.total_seconds() / 60).le(60)
    )
    close_counts = (
        close_time.groupby(time_sorted["passenger_id"])
        .sum()
        .rename("close_time_cnt")
    )

    amount_stats = refunds.groupby(keys)["amount"].agg(["mean", "std", "count"])
    cv = (amount_stats["std"] / amount_stats["mean"]).where(
        (amount_stats["count"] >= 2) & amount_stats["mean"].gt(0),
        0,
    )
    amount_diversity = cv.groupby(level="passenger_id").max().clip(lower=1.0)

    result = (
        pd.concat([similar_counts, close_counts, amount_diversity.rename("refund_amount_diversity")], axis=1)
        .fillna({"similar_amount_cnt": 0, "close_time_cnt": 0, "refund_amount_diversity": 1.0})
        .reset_index()
    )
    result["suspicious_refund_pattern_cnt"] = (
        result["similar_amount_cnt"] + result["close_time_cnt"]
    ).astype(int)
    return result[
        ["passenger_id", "suspicious_refund_pattern_cnt", "refund_amount_diversity"]
    ]
