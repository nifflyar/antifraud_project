"""ML Service for Passenger Risk Scoring - Orchestrator."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text

# Import new modules
from app import fraud_scoring_v2, features, identity, seat_blocking, scoring, reasoning, operations, concentration, ml_model

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://passenger:passenger@localhost:5433/passenger_risk")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

app = FastAPI(title="Passenger Risk ML Service", version="0.2.0")


class ScoreRequest(BaseModel):
    upload_id: int | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


def _safe_float(value: Any) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _load_transactions(upload_id: int | None) -> pd.DataFrame:
    query = """
        SELECT
          t.*,
          p.fio_clean,
          p.fake_fio_score AS fio_fake_score
        FROM transactions t
        LEFT JOIN passengers p ON p.id = t.passenger_id
    """
    params = None
    if upload_id is not None:
        query += " WHERE t.upload_id = %(upload_id)s"
        params = {"upload_id": upload_id}
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params=params)

    if "op_type" in df.columns:
        df["op_type"] = df["op_type"].astype(str).str.strip().str.lower()

    for col in ["op_datetime", "dep_datetime"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _build_all_features(df: pd.DataFrame, upload_id: int | None) -> pd.DataFrame:
    """Build all features including enhanced ones."""
    if df.empty:
        return pd.DataFrame()

    # Build base features
    feat_df = features.build_enhanced_features(df, upload_id)
    feat_df["passenger_id"] = feat_df["passenger_id"].astype(str)

    # Add enhanced fake FIO scores using v2 high-precision detection
    fio_scores = []
    for passenger_id, group in df.groupby("passenger_id", dropna=False):
        row = group.iloc[0]
        raw_fio = row.get("fio")
        fio_clean = row.get("fio_clean")
        score, reasons = fraud_scoring_v2.fake_fio_score_detailed(raw_fio, fio_clean)
        fio_scores.append({"passenger_id": str(passenger_id), "fio_fake_score_new": score})

    if fio_scores:
        fio_df = pd.DataFrame(fio_scores)
        feat_df = feat_df.merge(fio_df, on="passenger_id", how="left")
        # Replace old score with new one, defaulting to 0
        if "fio_fake_score_max" in feat_df.columns:
            feat_df["fio_fake_score_max"] = feat_df["fio_fake_score_new"].fillna(feat_df["fio_fake_score_max"]).fillna(0)
        else:
            feat_df["fio_fake_score_max"] = feat_df["fio_fake_score_new"].fillna(0)

    # Add identity consistency features
    consistency = identity.build_identity_consistency_features(df)
    consistency_df = pd.DataFrame.from_dict(consistency, orient="index").reset_index()
    consistency_df.columns = [
        "passenger_id",
        "same_iin_multiple_fio",
        "same_doc_multiple_fio",
        "same_fio_multiple_iin",
        "same_fio_multiple_doc",
        "missing_identity_flag",
        "consistency_risk_score",
        "consistency_issues",
    ]
    consistency_df["passenger_id"] = consistency_df["passenger_id"].astype(str)
    feat_df = feat_df.merge(consistency_df, on="passenger_id", how="left")
    # Fill missing identity features with defaults
    feat_df["same_iin_multiple_fio"] = feat_df["same_iin_multiple_fio"].fillna(0).astype(int)
    feat_df["same_doc_multiple_fio"] = feat_df["same_doc_multiple_fio"].fillna(0).astype(int)
    feat_df["same_fio_multiple_iin"] = feat_df["same_fio_multiple_iin"].fillna(0).astype(int)
    feat_df["same_fio_multiple_doc"] = feat_df["same_fio_multiple_doc"].fillna(0).astype(int)
    feat_df["missing_identity_flag"] = feat_df["missing_identity_flag"].fillna(False).astype(bool)
    feat_df["consistency_risk_score"] = feat_df["consistency_risk_score"].fillna(0)

    # Add seat-blocking scores
    blocking = seat_blocking.detect_seat_blocking(df)
    blocking_df = pd.DataFrame.from_dict(blocking, orient="index").reset_index()
    blocking_df.columns = [
        "passenger_id",
        "seat_blocking_score",
        "seat_blocking_flag",
        "block_signals",
        "cluster_metrics",
        "issues",
    ]
    blocking_df["passenger_id"] = blocking_df["passenger_id"].astype(str)
    feat_df = feat_df.merge(blocking_df, on="passenger_id", how="left")
    # Fill missing seat-blocking features with defaults
    feat_df["seat_blocking_score"] = feat_df["seat_blocking_score"].fillna(0)
    feat_df["seat_blocking_flag"] = feat_df["seat_blocking_flag"].fillna(False).astype(bool)

    # Ensure all required NOT NULL columns exist with defaults
    required_cols = {
        "same_iin_multiple_fio": 0,
        "same_doc_multiple_fio": 0,
        "same_fio_multiple_iin": 0,
        "same_fio_multiple_doc": 0,
        "missing_identity_flag": False,
        "consistency_risk_score": 0,
    }
    for col, default_val in required_cols.items():
        if col not in feat_df.columns:
            feat_df[col] = default_val

    return feat_df


def _add_scores(all_features: pd.DataFrame) -> pd.DataFrame:
    """Add rule-based, ML, and final scores."""
    if all_features.empty:
        return all_features

    feat_df = all_features.copy()

    # Preserve identity consistency columns
    identity_cols = [
        "same_iin_multiple_fio",
        "same_doc_multiple_fio",
        "same_fio_multiple_iin",
        "same_fio_multiple_doc",
        "missing_identity_flag",
        "consistency_risk_score",
    ]
    preserved = {col: feat_df[col] if col in feat_df.columns else None for col in identity_cols}

    # 1. Calculate component scores
    feat_df = scoring.calculate_component_scores(feat_df)

    # Preliminary rule score is needed by the ML layer for contamination
    # estimation and fallback blending. calculate_final_score recalculates the
    # same value later, but ML must not receive an all-zero placeholder here.
    feat_df["rule_score"] = (
        feat_df["refund_score"] * 0.25
        + feat_df["timing_score"] * 0.15
        + feat_df["seat_blocking_score"] * 0.25
        + feat_df["identity_score"] * 0.15
        + feat_df["volume_score"] * 0.10
        + feat_df["repetition_score"] * 0.10
    ).clip(0, 100)

    # 2. Build ML model
    ml_scores, _ = ml_model.build_and_score_ml_model(
        feat_df, feat_df["rule_score"] if "rule_score" in feat_df.columns else pd.Series(0, index=feat_df.index)
    )
    feat_df["ml_score"] = ml_scores

    # 3. Calculate final score with gating
    feat_df = scoring.calculate_final_score(feat_df, ml_scores)

    # 4. Add structured reasons
    feat_df["top_reasons"] = feat_df.apply(
        lambda row: reasoning.build_top_reasons(row), axis=1
    )

    # 5. Ensure seat_blocking_flag exists
    if "seat_blocking_flag" not in feat_df.columns:
        feat_df["seat_blocking_flag"] = False

    # 6. Restore preserved identity consistency columns
    for col, vals in preserved.items():
        if vals is not None and col not in feat_df.columns:
            feat_df[col] = vals

    return feat_df


def _write_features_and_scores(features_df: pd.DataFrame) -> None:
    """Write features and scores to database."""
    feature_cols = [
        "passenger_id",
        "upload_id",
        "total_ops",
        "total_tickets",
        "sale_cnt",
        "paid_cnt",
        "refund_cnt",
        "refund_share",
        "paid_refund_share",
        "night_tickets",
        "night_share",
        "max_tickets_month",
        "max_tickets_same_depday",
        "refund_close_ratio",
        "tickets_per_train_peak",
        "fio_fake_score_max",
        "terminal_count",
        "cashdesk_count",
        "channel_count",
        "aggregator_count",
        "amount_sum",
        "amount_refunded",
        "rapid_cancel_cnt",
        "technical_cancel_cnt",
        "suspicious_refund_pattern_cnt",
        "refund_amount_diversity",
        "seat_blocking_score",
        "same_iin_multiple_fio",
        "same_doc_multiple_fio",
        "same_fio_multiple_iin",
        "same_fio_multiple_doc",
        "missing_identity_flag",
        "consistency_risk_score",
        "avg_minutes_to_departure_for_refunds",
    ]

    score_cols = [
        "passenger_id",
        "upload_id",
        "rule_score",
        "ml_score",
        "final_score",
        "risk_band",
        "top_reasons",
        "seat_blocking_flag",
        "scored_at",
    ]

    now = datetime.utcnow()

    # Prepare feature rows
    available_feature_cols = [c for c in feature_cols if c in features_df.columns]
    feat_df = features_df[available_feature_cols].copy()

    # Ensure NOT NULL columns have defaults
    not_null_defaults = {
        "fio_fake_score_max": 0,
        "same_iin_multiple_fio": 0,
        "same_doc_multiple_fio": 0,
        "same_fio_multiple_iin": 0,
        "same_fio_multiple_doc": 0,
        "consistency_risk_score": 0,
        "seat_blocking_score": 0,
        "missing_identity_flag": False,
    }
    for col, default in not_null_defaults.items():
        if col in feat_df.columns:
            feat_df[col] = feat_df[col].fillna(default)

    feat_rows = (
        feat_df
        .replace({np.nan: None})
        .to_dict(orient="records")
    )

    # Prepare score rows
    score_df = features_df.copy()
    score_df["scored_at"] = now
    if "top_reasons" in score_df.columns:
        score_df["top_reasons"] = score_df["top_reasons"].apply(json.dumps)
    score_rows = (
        score_df[score_cols]
        .replace({np.nan: None})
        .to_dict(orient="records")
    )

    with engine.begin() as conn:
        if feat_rows:
            # Build dynamic INSERT for available columns
            col_list = ", ".join(available_feature_cols)
            val_list = ", ".join([f":{c}" for c in available_feature_cols])
            update_list = ", ".join([f"{c} = EXCLUDED.{c}" for c in available_feature_cols if c != "passenger_id"])

            conn.execute(
                text(f"""
                    INSERT INTO passenger_features ({col_list})
                    VALUES ({val_list})
                    ON CONFLICT (passenger_id) DO UPDATE SET {update_list}
                """),
                feat_rows,
            )

        if score_rows:
            conn.execute(
                text("""
                    INSERT INTO passenger_scores
                    (passenger_id, upload_id, rule_score, ml_score, final_score, risk_band, top_reasons, seat_blocking_flag, scored_at)
                    VALUES
                    (:passenger_id, :upload_id, :rule_score, :ml_score, :final_score, :risk_band, CAST(:top_reasons AS JSON), :seat_blocking_flag, :scored_at)
                    ON CONFLICT (passenger_id) DO UPDATE SET
                      upload_id = EXCLUDED.upload_id,
                      rule_score = EXCLUDED.rule_score,
                      ml_score = EXCLUDED.ml_score,
                      final_score = EXCLUDED.final_score,
                      risk_band = EXCLUDED.risk_band,
                      top_reasons = EXCLUDED.top_reasons,
                      seat_blocking_flag = EXCLUDED.seat_blocking_flag,
                      scored_at = EXCLUDED.scored_at
                """),
                score_rows,
            )


def _write_concentration(df: pd.DataFrame, scores_df: pd.DataFrame) -> int:
    """Calculate and write risk concentration metrics."""
    if df.empty or scores_df.empty:
        return 0

    # Get concentration data
    concentration_records = concentration.calculate_risk_concentration(df, scores_df)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM risk_concentration"))
        if concentration_records:
            conn.execute(
                text("""
                    INSERT INTO risk_concentration
                    (dimension_type, dimension_value, total_ops, highrisk_ops, critical_ops,
                     share_highrisk_ops, share_critical_ops, lift_vs_base, base_highrisk_share,
                     total_amount, suspicious_amount, calculated_at)
                    VALUES
                    (:dimension_type, :dimension_value, :total_ops, :highrisk_ops, :critical_ops,
                     :share_highrisk_ops, :share_critical_ops, :lift_vs_base, :base_highrisk_share,
                     :total_amount, :suspicious_amount, :calculated_at)
                """),
                [
                    {
                        **rec,
                        "calculated_at": datetime.utcnow(),
                    }
                    for rec in concentration_records
                ],
            )

    return len(concentration_records)


@app.post("/score")
def score(request: ScoreRequest):
    df = _load_transactions(request.upload_id)
    if df.empty:
        return {
            "status": "empty",
            "upload_id": request.upload_id,
            "passengers_scored": 0,
        }

    all_features = _build_all_features(df, request.upload_id)
    all_features = _add_scores(all_features)

    risk_counts = all_features["risk_band"].value_counts().to_dict()
    seat_blocking_cases = int(all_features["seat_blocking_flag"].sum())
    results = [_feature_row_to_result(row) for _, row in all_features.iterrows()]

    return {
        "status": "success",
        "upload_id": request.upload_id,
        "passengers_scored": int(len(all_features)),
        "risk_counts": risk_counts,
        "seat_blocking_cases": seat_blocking_cases,
        "concentration_rows": 0,
        "results": results,
    }


def _safe_int(value: Any) -> int:
    try:
        if value is None or pd.isna(value):
            return 0
        return int(value)
    except Exception:
        return 0


def _feature_row_to_result(row: pd.Series) -> dict[str, Any]:
    top_reasons = row.get("top_reasons", [])
    if isinstance(top_reasons, str):
        try:
            top_reasons = json.loads(top_reasons)
        except Exception:
            top_reasons = [top_reasons]

    return {
        "passenger_id": _safe_int(row.get("passenger_id")),
        "rule_score": _safe_float(row.get("rule_score")),
        "ml_score": _safe_float(row.get("ml_score")),
        "final_score": _safe_float(row.get("final_score")),
        "risk_band": str(row.get("risk_band", "LOW")).lower(),
        "top_reasons": list(top_reasons)[:6],
        "total_tickets": _safe_int(row.get("total_tickets")),
        "refund_cnt": _safe_int(row.get("refund_cnt")),
        "refund_share": _safe_float(row.get("refund_share")),
        "night_tickets": _safe_int(row.get("night_tickets")),
        "night_share": _safe_float(row.get("night_share")),
        "max_tickets_month": _safe_int(row.get("max_tickets_month")),
        "max_tickets_same_depday": _safe_int(row.get("max_tickets_same_depday")),
        "tickets_per_train_peak": _safe_float(row.get("tickets_per_train_peak")),
        "late_refunds": _safe_int(row.get("close_refund_cnt")),
        "late_refund_share": _safe_float(row.get("refund_close_ratio")),
        "very_late_refunds": _safe_int(row.get("very_close_refund_cnt")),
        "very_late_refund_share": _safe_float(row.get("very_close_refund_cnt")) / max(_safe_int(row.get("refund_cnt")), 1),
        "quick_refunds": _safe_int(row.get("rapid_cancel_cnt")),
        "quick_refund_share": _safe_float(row.get("rapid_cancel_cnt")) / max(_safe_int(row.get("refund_cnt")), 1),
        "activity_days": _safe_int(row.get("activity_days")) or 1,
        "suspicious_refund_pattern_cnt": _safe_int(row.get("suspicious_refund_pattern_cnt")),
        "refund_amount_diversity": _safe_float(row.get("refund_amount_diversity")) or 1.0,
        "seat_blocking_flag": bool(row.get("seat_blocking_flag", False)),
        "refund_close_ratio": _safe_float(row.get("refund_close_ratio")),
        "fake_fio": _safe_float(row.get("fio_fake_score_max")),
    }
