"""Improved ML model for anomaly detection."""

from typing import Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler
from sklearn.preprocessing import StandardScaler


def _robust_behavioral_anomaly_score(features: pd.DataFrame) -> pd.Series:
    """Explainable unsupervised pressure score from extreme behavioral features.

    This complements IsolationForest: IF can miss "dense but extreme" users when
    several heavy users exist in the same batch. Percentile/max-feature pressure
    keeps unknown large-footprint anomalies visible without hand-writing a single
    fraud rule for every case.
    """
    if features.empty:
        return pd.Series(dtype=float)

    pressure_specs = {
        # column: (weight, minimum absolute value). The minimum keeps the model
        # from treating ordinary low-volume behavior as suspicious just because
        # it is uncommon in the current upload.
        "total_ops": (1.00, 20),
        "total_tickets": (1.00, 10),
        "refund_cnt": (0.90, 5),
        "suspicious_refund_pattern_cnt": (1.00, 3),
        "max_tickets_same_depday": (1.00, 8),
        "tickets_per_train_peak": (1.00, 5),
        "terminal_count": (0.75, 4),
        "cashdesk_count": (0.65, 4),
        "channel_count": (0.45, 3),
        "aggregator_count": (0.45, 2),
        "amount_sum": (0.55, 50_000),
        "amount_refunded": (0.70, 20_000),
        "rapid_cancel_cnt": (0.90, 2),
        "technical_cancel_cnt": (0.80, 2),
        "seat_blocking_score": (1.00, 30),
        "consistency_risk_score": (0.85, 20),
        "fio_fake_score_max": (0.75, 5),
    }

    scores = []
    for col, (weight, min_value) in pressure_specs.items():
        if col not in features.columns:
            continue
        values = (
            features[col]
            .replace([np.inf, -np.inf], 0)
            .fillna(0)
            .astype(float)
        )
        if values.nunique() <= 1:
            continue

        percentile = values.rank(pct=True) * 100
        percentile_score = ((percentile - 90.0) / 10.0 * 100).clip(lower=0, upper=100)
        median = values.median()
        mad = (values - median).abs().median()
        if mad and mad > 0:
            robust_z = ((values - median) / (1.4826 * mad)).clip(lower=0)
            z_score = (1 - np.exp(-robust_z / 4.0)) * 100
        else:
            z_score = pd.Series(0.0, index=values.index)

        eligible = values >= min_value
        col_score = np.where(eligible, np.maximum(percentile_score, z_score) * weight, 0)
        scores.append(pd.Series(col_score, index=features.index))

    if not scores:
        return pd.Series(0.0, index=features.index)

    pressure = pd.concat(scores, axis=1).max(axis=1).clip(0, 100)

    # Bonuses for multi-signal anomalies. These are generic combinations of
    # independent dimensions, not narrow fraud scripts.
    if {"total_tickets", "terminal_count"}.issubset(features.columns):
        pressure = np.where(
            (features["total_tickets"].fillna(0) >= 50)
            & (features["terminal_count"].fillna(0) >= 5),
            np.maximum(pressure, 88),
            pressure,
        )
    if {"refund_cnt", "suspicious_refund_pattern_cnt"}.issubset(features.columns):
        pressure = np.where(
            (features["refund_cnt"].fillna(0) >= 10)
            & (features["suspicious_refund_pattern_cnt"].fillna(0) >= 5),
            np.maximum(pressure, 85),
            pressure,
        )
    if {"max_tickets_same_depday", "tickets_per_train_peak"}.issubset(features.columns):
        pressure = np.where(
            (features["max_tickets_same_depday"].fillna(0) >= 20)
            | (features["tickets_per_train_peak"].fillna(0) >= 10),
            np.maximum(pressure, 85),
            pressure,
        )

    return pd.Series(pressure, index=features.index).astype(float)


def build_and_score_ml_model(
    features: pd.DataFrame,
    rule_scores: pd.Series,
    contamination: float = 0.05,
    random_state: int = 42,
) -> Tuple[pd.Series, pd.Series]:
    """
    Build ML anomaly detection model and return anomaly scores.

    Uses Isolation Forest with fallback to LOF for small datasets.
    Incorporates rule-based scores for better contamination estimation.

    Args:
        features: DataFrame with feature columns
        rule_scores: Series with rule-based scores
        contamination: Contamination rate for IF
        random_state: Random seed for reproducibility

    Returns:
        (ml_scores, feature_contributions): ml_scores in [0, 100], feature_contributions
    """

    model_cols = [
        "total_tickets",
        "sale_cnt",
        "refund_cnt",
        "refund_share",
        "paid_refund_share",
        "night_share",
        "max_tickets_month",
        "max_tickets_same_depday",
        "refund_close_ratio",
        "tickets_per_train_peak",
        "fio_fake_score_max",
        "terminal_count",
        "channel_count",
        "aggregator_count",
        "amount_sum",
        "amount_refunded",
        "rapid_cancel_cnt",
        "technical_cancel_cnt",
        "suspicious_refund_pattern_cnt",
        "refund_amount_diversity",
        "seat_blocking_score",
        "consistency_risk_score",
        "cashdesk_count",
    ]

    # Filter to available columns
    available_cols = [c for c in model_cols if c in features.columns]

    if len(features) < 10 or len(available_cols) < 5:
        pressure = _robust_behavioral_anomaly_score(features)
        return pd.Series(np.maximum(rule_scores.copy() * 0.9, pressure), index=features.index), pd.Series([0.0] * len(features))

    X = features[available_cols].copy()

    # Handle missing and infinite values
    X = X.replace([np.inf, -np.inf], 0).fillna(0).astype(float)

    # Check if there's actual variance
    if X.nunique().sum() <= len(available_cols):
        pressure = _robust_behavioral_anomaly_score(features)
        return pd.Series(np.maximum(rule_scores.copy() * 0.9, pressure), index=features.index), pd.Series([0.0] * len(features))

    # Log transform skewed distributions
    X_transformed = X.copy()
    for col in X_transformed.columns:
        if X_transformed[col].min() >= 0:
            X_transformed[col] = np.log1p(X_transformed[col])

    # Scale features
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_transformed)

    # Estimate better contamination from rule scores
    critical_rules = (rule_scores >= 80).sum()
    high_rules = (rule_scores >= 60).sum()
    estimated_contamination = min(0.10, max(0.02, (critical_rules + high_rules * 0.5) / len(features)))

    # Build model - try Isolation Forest first
    pressure = _robust_behavioral_anomaly_score(features).reindex(features.index).fillna(0)
    try:
        clf = IsolationForest(
            n_estimators=250,
            contamination=estimated_contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        clf.fit(X_scaled)
        raw_scores = -clf.decision_function(X_scaled)
    except Exception:
        # Fallback to LOF if IF fails
        try:
            lof = LocalOutlierFactor(
                n_neighbors=min(20, len(features) - 1),
                contamination=estimated_contamination,
            )
            lof.fit_predict(X_scaled)
            raw_scores = -lof.negative_outlier_factor_
        except Exception:
            # If both statistical models fail, still preserve the robust
            # behavioral pressure so clear anomalies do not become ML=0.
            fallback = np.maximum(rule_scores.copy() * 0.9, pressure)
            return pd.Series(fallback, index=features.index), pd.Series([0.0] * len(features))

    # Normalize to [0, 100]
    raw_scores = raw_scores.reshape(-1)

    # Percentile rank, calibrated so only the upper tail becomes a strong ML
    # anomaly. A 50th percentile case should not display as ML=50.
    model_percentile = pd.Series(raw_scores).rank(pct=True).to_numpy() * 100
    ml_scores = np.clip((model_percentile - 90.0) / 10.0 * 100, 0, 100)

    pressure_scores = pressure.to_numpy()
    corroborated = (
        (pressure_scores >= 50)
        | (rule_scores.values >= 20)
    )
    model_signal = np.where(corroborated, ml_scores, np.minimum(ml_scores, 25))

    # Blend model, robust behavioral anomaly and rules. Use max to preserve
    # strong unknown anomalies even if the forest considers them part of a dense
    # cluster.
    blended = np.maximum.reduce([
        model_signal,
        pressure_scores,
        0.60 * rule_scores.values + 0.40 * model_signal,
    ])

    return pd.Series(blended, index=features.index), pd.Series(
        [0.0] * len(features)
    )  # TODO: Add feature importance extraction


def calculate_contamination_from_rules(rule_scores: pd.Series) -> float:
    """Estimate contamination rate from rule-based scores."""
    critical = (rule_scores >= 80).sum()
    high = (rule_scores >= 60).sum()
    medium = (rule_scores >= 40).sum()

    # Assume high and critical are true anomalies, medium is borderline
    total_anomalies = critical + high * 0.5 + medium * 0.2
    rate = total_anomalies / len(rule_scores)

    # Clamp between reasonable bounds
    return min(0.15, max(0.02, rate))
