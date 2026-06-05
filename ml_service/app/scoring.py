"""Component-based risk scoring with critical gating and contextual validation."""

import pandas as pd
import numpy as np
try:
    from .fraud_scoring_v2 import fake_fio_score_detailed
    from .contextual_validation import (
        apply_contextual_validation,
        count_independent_signals,
        has_core_fraud_evidence,
    )
except ImportError:
    from fraud_scoring_v2 import fake_fio_score_detailed
    from contextual_validation import (
        apply_contextual_validation,
        count_independent_signals,
        has_core_fraud_evidence,
    )


def calculate_component_scores(features: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate individual component scores (0-100).

    Components:
    - refund_score: count, share, timing, diversity
    - timing_score: night activity, clustering
    - seat_blocking_score: from seat_blocking module
    - identity_score: fake FIO + consistency
    - volume_score: tickets concentration
    - repetition_score: across trains/days

    Args:
        features: DataFrame with all feature columns

    Returns:
        DataFrame with component_* columns added
    """
    df = features.copy()

    # 1. REFUND SCORE (0-100) - FOCUS ON ANOMALIES
    refund_score = pd.Series(0, index=df.index)

    # Refund count - penalize high volumes heavily, ignore low volumes
    refund_score += np.where(df["refund_cnt"] >= 10, 25, 0)
    refund_score += np.where(
        (df["refund_cnt"] >= 5) & (df["refund_cnt"] < 10), 15, 0
    )
    refund_score += np.where(
        (df["refund_cnt"] >= 3) & (df["refund_cnt"] < 5), 5, 0
    )

    # Refund share - only care if there are enough total ops
    high_volume_refunds = (df["total_ops"] >= 4)
    refund_score += np.where(high_volume_refunds & (df["refund_share"] >= 0.80), 20, 0)
    refund_score += np.where(high_volume_refunds & (df["refund_share"] >= 0.60) & (df["refund_share"] < 0.80), 10, 0)

    # Close refunds - strong indicator only if > 2 refunds
    refund_score += np.where(
        (df["refund_close_ratio"] >= 0.50) & (df["refund_cnt"] >= 3), 15, 0
    )

    # Suspicious refund patterns (multiple similar amounts on same day)
    # INCREASE THIS WEIGHT as it's the core anomaly signal
    refund_score += np.where(
        df.get("suspicious_refund_pattern_cnt", 0) >= 3, 40, 0
    )
    refund_score += np.where(
        (df.get("suspicious_refund_pattern_cnt", 0) == 2), 25, 0
    )
    refund_score += np.where(
        (df.get("suspicious_refund_pattern_cnt", 0) == 1), 10, 0
    )

    # Amount diversity penalty (same route/price suggests automated scripts)
    refund_score += np.where(
        (df.get("refund_amount_diversity", 1.0) < 0.10) & (df["refund_cnt"] >= 3), 20, 0
    )

    df["refund_score"] = refund_score.clip(0, 100)

    # 2. TIMING SCORE (0-100)
    timing_score = pd.Series(0, index=df.index)

    # Night activity
    timing_score += np.where(
        (df["night_share"] >= 0.50) & (df["total_tickets"] >= 5), 15, 0
    )
    timing_score += np.where(
        (df["night_share"] >= 0.30) & (df["total_tickets"] >= 3), 8, 0
    )

    # Close refunds - moderate weight
    timing_score += np.where(df["refund_close_ratio"] >= 0.50, 10, 0)
    timing_score += np.where((df["refund_close_ratio"] >= 0.30) & (df["refund_close_ratio"] < 0.50), 5, 0)

    df["timing_score"] = timing_score.clip(0, 100)

    # 3. IDENTITY SCORE (0-100) - Using v2 high-precision detection
    identity_score = pd.Series(0, index=df.index)

    # Use v2 fraud scoring for better precision (0-10 scale)
    # Note: Assumes fio_fake_score_max is already calculated by features.py
    # using fake_fio_score_detailed from fraud_scoring_v2

    # Map v2 scores (0-10) to component score (0-100) with better calibration
    # 0-2: Normal (0 points)
    # 3-4: Minor oddities (10-20 points)
    # 5-7: Moderate concerns (30-50 points)
    # 8-10: High confidence fake (60-100 points)
    def map_fake_fio_to_component(fio_score):
        if fio_score <= 2:
            return 0
        elif fio_score <= 4:
            return 15
        elif fio_score <= 7:
            return 40
        else:  # 8-10
            return 70

    identity_score = df["fio_fake_score_max"].apply(map_fake_fio_to_component)

    # Missing identity
    identity_score += np.where(
        df.get("missing_identity_flag", False), 15, 0
    )

    # Consistency issues (if available)
    if "consistency_risk_score" in df.columns:
        identity_score += df["consistency_risk_score"] * 0.5

    df["identity_score"] = identity_score.clip(0, 100)

    # 4. VOLUME SCORE (0-100)
    volume_score = pd.Series(0, index=df.index)

    volume_score += np.where(df["max_tickets_same_depday"] >= 10, 25, 0)
    volume_score += np.where(
        (df["max_tickets_same_depday"] >= 6) & (df["max_tickets_same_depday"] < 10), 15, 0
    )
    volume_score += np.where(
        (df["max_tickets_same_depday"] >= 3) & (df["max_tickets_same_depday"] < 6), 8, 0
    )

    volume_score += np.where(df["max_tickets_month"] >= 20, 15, 0)
    volume_score += np.where(
        (df["max_tickets_month"] >= 12) & (df["max_tickets_month"] < 20), 10, 0
    )

    df["volume_score"] = volume_score.clip(0, 100)

    # 5. REPETITION SCORE (0-100)
    repetition_score = pd.Series(0, index=df.index)

    # Rapid cancellations (within 10 mins)
    repetition_score += np.where(df["rapid_cancel_cnt"] >= 3, 20, 0)
    repetition_score += np.where(
        (df["rapid_cancel_cnt"] >= 1) & (df["rapid_cancel_cnt"] < 3), 8, 0
    )

    # Technical cancellations
    repetition_score += np.where(df["technical_cancel_cnt"] >= 2, 15, 0)
    repetition_score += np.where(df["technical_cancel_cnt"] == 1, 8, 0)

    df["repetition_score"] = repetition_score.clip(0, 100)

    # 6. SEAT BLOCKING SCORE (already computed, just ensure it exists)
    if "seat_blocking_score" not in df.columns:
        df["seat_blocking_score"] = 0

    return df


def calculate_final_score(features: pd.DataFrame, ml_scores: pd.Series) -> pd.DataFrame:
    """
    Calculate final risk score with component blending and critical gating.

    Args:
        features: DataFrame with component scores and features
        ml_scores: ML anomaly scores (0-100)

    Returns:
        DataFrame with rule_score, ml_score, final_score, risk_band columns
    """
    df = features.copy()

    # Ensure all component scores exist
    components = [
        "refund_score",
        "timing_score",
        "identity_score",
        "volume_score",
        "repetition_score",
        "seat_blocking_score",
    ]
    for comp in components:
        if comp not in df.columns:
            df[comp] = 0

    # 1. CALCULATE RULE SCORE (weighted average)
    rule_score = (
        df["refund_score"] * 0.25
        + df["timing_score"] * 0.15
        + df["seat_blocking_score"] * 0.25
        + df["identity_score"] * 0.15
        + df["volume_score"] * 0.10
        + df["repetition_score"] * 0.10
    )

    df["rule_score"] = rule_score.clip(0, 100)

    # 2. MERGE ML SCORES
    df["ml_score"] = ml_scores.values

    pattern_cnt = df.get("suspicious_refund_pattern_cnt", pd.Series(0, index=df.index))
    terminal_count = df.get("terminal_count", pd.Series(0, index=df.index))
    total_ops = df.get("total_ops", df.get("total_tickets", pd.Series(0, index=df.index)))

    # ML can flag statistically rare but legitimate low-volume behavior. Let it
    # influence final risk strongly only when there is a business corroboration
    # signal: volume, identity issue, refund clustering, seat blocking, or
    # operational footprint.
    ml_corrob = (
        (df["rule_score"] >= 20)
        | (df["refund_cnt"] >= 5)
        | (pattern_cnt >= 3)
        | (df["identity_score"] >= 40)
        | (df["seat_blocking_score"] >= 50)
        | (df["total_tickets"] >= 20)
        | (df["max_tickets_same_depday"] >= 10)
        | (terminal_count >= 5)
        | (df["rapid_cancel_cnt"] >= 2)
        | (df["technical_cancel_cnt"] >= 2)
    )
    effective_ml_score = np.where(ml_corrob, df["ml_score"], np.minimum(df["ml_score"], 25))

    # 3. BLEND RULE + ML (0.65 rule, 0.35 calibrated ML)
    blended_score = 0.65 * df["rule_score"] + 0.35 * effective_ml_score

    # 4. APPLY CRITICAL GATING
    final_score = blended_score.copy()

    # Signal 1: Strong seat blocking with timing
    signal1 = (
        (df["seat_blocking_score"] >= 70)
        & (df["refund_close_ratio"] >= 0.30)
        | ((df["seat_blocking_score"] >= 75) & (df["paid_refund_share"] >= 0.30))
    )
    final_score = np.where(signal1, np.maximum(final_score, 80), final_score)

    # Signal 2: High refund abuse or organized suspicious refund patterns.
    # Two same-day refunds alone are not enough for HIGH risk: this can be a
    # normal return/round-trip correction. Require either 3+ clustered refunds
    # or a second corroborating signal.
    organized_refund_pattern = (
        ((pattern_cnt >= 3) & (df["refund_cnt"] >= 3))
        | (
            (pattern_cnt >= 2)
            & (
                (df["refund_cnt"] >= 4)
                | (df["refund_close_ratio"] >= 0.40)
                | (df["rapid_cancel_cnt"] >= 2)
                | (df["technical_cancel_cnt"] >= 2)
                | (df["seat_blocking_score"] >= 50)
                | (df["identity_score"] >= 40)
            )
        )
    )
    signal2 = (
        organized_refund_pattern
        | ((df["paid_refund_share"] >= 0.50) & (df["refund_cnt"] >= 5) & (df["refund_close_ratio"] >= 0.40))
    )
    final_score = np.where(signal2, np.maximum(final_score, 80), final_score)

    # Signal 3: Severe fake identity with behavioral corroboration. A suspicious
    # or placeholder name alone is not fraud; it becomes actionable only when
    # paired with refunds, concentration, terminal spread, or identity mismatch.
    identity_corrob = (
        (df["refund_cnt"] >= 3)
        | (pattern_cnt >= 3)
        | (df["total_tickets"] >= 20)
        | (df["max_tickets_same_depday"] >= 10)
        | (terminal_count >= 5)
        | (df["seat_blocking_score"] >= 50)
        | (df.get("consistency_risk_score", 0) >= 20)
    )
    signal3 = (df["fio_fake_score_max"] >= 8) & identity_corrob
    final_score = np.where(signal3, np.maximum(final_score, 60), final_score)

    # Signal 4: ML + Rule score alignment for anomalies
    signal4 = (df["ml_score"] >= 85) & (df["rule_score"] >= 60)
    final_score = np.where(signal4, np.maximum(final_score, 75), final_score)

    # Signal 5: unknown large-footprint anomaly. This is intentionally generic:
    # many tickets/operations across terminals/trains plus any refund, identity
    # or clustering signal should be reviewed even when it does not match a
    # named fraud pattern.
    extreme_volume = (
        (df["total_tickets"] >= 100)
        | (total_ops >= 200)
        | (df["max_tickets_same_depday"] >= 50)
        | (df["tickets_per_train_peak"] >= 10)
    )
    footprint_corruption = (
        (terminal_count >= 10)
        | (df["refund_cnt"] >= 10)
        | (pattern_cnt >= 10)
        | (df["identity_score"] >= 40)
        | (df["seat_blocking_score"] >= 50)
    )
    signal5 = extreme_volume & footprint_corruption
    final_score = np.where(signal5, np.maximum(final_score, 85), final_score)

    # 5. FALSE POSITIVE CONTROL - CAP SCORES WITHOUT CRITICAL SIGNALS
    critical_signals = signal1.astype(int) + signal2.astype(int) + signal3.astype(int) + signal4.astype(int) + signal5.astype(int)

    # No critical signals: cap at 75 (was 79, more lenient)
    final_score = np.where(critical_signals == 0, np.minimum(final_score, 75), final_score)

    # Only 1 signal: cap at 75 (was 79)
    final_score = np.where(critical_signals == 1, np.minimum(final_score, 75), final_score)

    # Additional false positive control - more lenient for normal behaviors
    # Normal returns: regardless of ratio, if count <= 3 and no anomalous patterns, cap aggressively
    normal_returns = (
        (df["refund_cnt"] > 0)
        & (df["refund_cnt"] <= 4)
        & (df.get("suspicious_refund_pattern_cnt", 0) == 0)
        & (df["rapid_cancel_cnt"] == 0)
        & (df["technical_cancel_cnt"] == 0)
        & (df["fio_fake_score_max"] <= 3)
        & (df["seat_blocking_score"] < 50)
    )
    final_score = np.where(normal_returns, np.minimum(final_score, 35), final_score)

    # Single refund without other signals = cap at 25
    single_refund_only = (
        (df["refund_cnt"] == 1)
        & (df["rapid_cancel_cnt"] == 0)
        & (df["technical_cancel_cnt"] == 0)
        & (df["fio_fake_score_max"] <= 3)
        & (df.get("suspicious_refund_pattern_cnt", 0) == 0)
        & (df["seat_blocking_score"] < 50)
    )
    final_score = np.where(single_refund_only, np.minimum(final_score, 25), final_score)

    # Two ordinary refunds without corroboration should remain LOW. This was a
    # known false positive class: rare in a batch, but explainable as regular
    # passenger corrections/returns.
    ordinary_low_volume_refunds = (
        (df["refund_cnt"] <= 2)
        & (pattern_cnt <= 2)
        & (df["total_tickets"] <= 6)
        & (df["rapid_cancel_cnt"] == 0)
        & (df["technical_cancel_cnt"] == 0)
        & (df["fio_fake_score_max"] <= 3)
        & (df["seat_blocking_score"] < 50)
        & (terminal_count <= 2)
        & (df["max_tickets_same_depday"] <= 4)
    )
    final_score = np.where(ordinary_low_volume_refunds, np.minimum(final_score, 25), final_score)

    df["final_score"] = final_score.clip(0, 100).astype(float)

    # 7. APPLY CONTEXTUAL VALIDATION (corroboration-based approach)
    # This is the key to reducing false positives - require multiple independent signals
    df = apply_contextual_validation(df)

    # 8. ADD SIGNAL COUNTING for better decision making
    df["independent_signals"] = df.apply(count_independent_signals, axis=1)

    # 9. ADD CORE FRAUD EVIDENCE FLAG. HIGH/CRITICAL require this so isolated
    # data-quality issues do not become fraud verdicts.
    df["core_fraud_evidence"] = df.apply(has_core_fraud_evidence, axis=1)

    # 10. ASSIGN RISK BANDS
    df["risk_band"] = _assign_risk_band_with_corroboration(df)

    return df


def _assign_risk_band_with_corroboration(df: pd.DataFrame) -> pd.Series:
    """Convert scores to risk bands with corroboration requirements.

    Risk assignment now considers:
    - final_score (after contextual caps)
    - independent_signals (count of distinct fraud indicators)
    - Corroboration requirement: need 2+ signals for HIGH/CRITICAL

    Risk bands:
    - LOW (0-50): low score, contextual exception, or identity-only issue
    - MEDIUM (50-70): final_score 50-70 AND 2+ signals
    - HIGH (70-85): final_score 70+ AND 2+ signals AND core fraud evidence
    - CRITICAL (85-100): final_score 85+ AND 3+ signals AND core fraud evidence
    """
    bands = pd.Series("LOW", index=df.index)

    final_score = df["final_score"]
    signals = df.get("independent_signals", pd.Series(1, index=df.index))
    core = df.get("core_fraud_evidence", pd.Series(False, index=df.index))

    # CRITICAL: Very high score + strong corroboration + actionable behavior.
    critical = (final_score >= 85) & (signals >= 3) & core
    bands[critical] = "CRITICAL"

    # HIGH: High score + at least 2 independent signals + actionable behavior.
    high = (final_score >= 70) & (final_score < 85) & (signals >= 2) & core
    bands[high] = "HIGH"

    # MEDIUM: Needs review, but lacks enough corroboration for high/critical.
    medium = (
        ((final_score >= 50) & (final_score < 70) & (signals >= 2))
        | ((final_score >= 70) & ((signals < 2) | ~core))
    )
    bands[medium] = "MEDIUM"

    # LOW: Default for anything else (low scores or single signals)
    # Already set above, just explicit for clarity

    return bands


def _assign_risk_band(scores: pd.Series) -> pd.Series:
    """Legacy risk band assignment (deprecated, use _assign_risk_band_with_corroboration)."""
    bands = pd.Series("LOW", index=scores.index)
    bands[scores >= 80] = "CRITICAL"
    bands[(scores >= 55) & (scores < 80)] = "HIGH"
    bands[(scores >= 30) & (scores < 55)] = "MEDIUM"
    return bands
