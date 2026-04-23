"""KPI computation engine for doctor performance."""
from __future__ import annotations
import pandas as pd
import numpy as np


def _consult_score(avg_min: float) -> float:
    return max(0.0, 100.0 - max(0.0, avg_min - 15.0) * 2.0)


def compute_kpis(df: pd.DataFrame, threshold: float = 60.0) -> pd.DataFrame:
    """Aggregate per-doctor KPIs and a composite score.

    Composite weights:
        success      30%
        satisfaction 25%   (scaled x10)
        diagnosis    25%
        low readmit  10%
        consult eff. 10%
    """
    g = df.groupby(["doctor_id", "doctor_name", "specialization"], as_index=False)
    out = g.agg(
        patients=("patient_id", "count"),
        success_rate=("treatment_outcome", lambda s: (s == "success").mean() * 100),
        satisfaction=("satisfaction_score", "mean"),
        avg_consultation=("consultation_time_min", "mean"),
        readmission_rate=("readmitted", lambda s: s.mean() * 100),
        diagnosis_accuracy=("diagnosis_correct", lambda s: s.mean() * 100),
    )
    out["composite"] = (
        out["success_rate"] * 0.30
        + out["satisfaction"] * 10 * 0.25
        + out["diagnosis_accuracy"] * 0.25
        + (100 - out["readmission_rate"]) * 0.10
        + out["avg_consultation"].apply(_consult_score) * 0.10
    )
    out["flagged"] = out["composite"] < threshold
    out = out.sort_values("composite", ascending=False).reset_index(drop=True)

    for col in ["success_rate", "readmission_rate", "diagnosis_accuracy", "composite"]:
        out[col] = out[col].round(1)
    out["satisfaction"] = out["satisfaction"].round(2)
    out["avg_consultation"] = out["avg_consultation"].round(1)
    return out


def monthly_success_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly success rate across the dataset."""
    d = df.copy()
    d["month"] = pd.to_datetime(d["date"]).dt.to_period("M").astype(str)
    out = d.groupby("month").agg(
        total=("patient_id", "count"),
        success=("treatment_outcome", lambda s: (s == "success").sum()),
    ).reset_index()
    out["success_rate"] = (out["success"] / out["total"] * 100).round(1)
    return out[["month", "success_rate"]]


def specialization_summary(kpis: pd.DataFrame) -> pd.DataFrame:
    return (
        kpis.groupby("specialization")
        .agg(
            doctors=("doctor_id", "count"),
            avg_composite=("composite", "mean"),
            avg_success=("success_rate", "mean"),
            avg_satisfaction=("satisfaction", "mean"),
            flagged=("flagged", "sum"),
        )
        .round(2)
        .reset_index()
        .sort_values("avg_composite", ascending=False)
    )
