"""Data cleaning & normalization."""
from __future__ import annotations
import pandas as pd
import numpy as np


def _to_bool(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().isin({"true", "1", "yes", "y"})


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize a doctor-patient dataset.

    - drop rows with missing doctor_id / patient_id
    - drop duplicate (doctor_id, patient_id, date) rows
    - normalize treatment_outcome to {success, partial, failure}
    - clamp satisfaction_score to 1..10
    - coerce numeric / bool / date columns
    """
    df = df.copy()

    df = df.dropna(subset=["doctor_id", "patient_id"])
    df["doctor_id"] = df["doctor_id"].astype(str).str.strip()
    df["patient_id"] = df["patient_id"].astype(str).str.strip()
    df["doctor_name"] = df.get("doctor_name", df["doctor_id"]).astype(str).str.strip()
    df["specialization"] = df.get("specialization", "General").astype(str).str.strip()

    outcome = df["treatment_outcome"].astype(str).str.lower().str.strip()
    df["treatment_outcome"] = outcome.where(outcome.isin(["success", "partial", "failure"]), "success")

    df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce").fillna(7).clip(1, 10)
    df["consultation_time_min"] = pd.to_numeric(df["consultation_time_min"], errors="coerce").fillna(20).clip(lower=1)
    df["readmitted"] = _to_bool(df["readmitted"])
    df["diagnosis_correct"] = _to_bool(df["diagnosis_correct"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype(str)

    df = df.drop_duplicates(subset=["doctor_id", "patient_id", "date"])
    return df.reset_index(drop=True)
