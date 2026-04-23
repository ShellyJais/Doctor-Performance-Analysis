"""Data ingestion: load CSV/Excel doctor-patient datasets."""
from __future__ import annotations
import pandas as pd
from pathlib import Path

REQUIRED_COLUMNS = [
    "doctor_id", "doctor_name", "specialization", "patient_id",
    "treatment_outcome", "satisfaction_score", "consultation_time_min",
    "readmitted", "diagnosis_correct", "date",
]


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load a dataset from CSV or Excel. Returns a raw DataFrame."""
    p = Path(path)
    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
    elif p.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(p)
    else:
        raise ValueError(f"Unsupported file type: {p.suffix}")
    return df


def validate_schema(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Return (is_valid, missing_columns)."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return (len(missing) == 0, missing)
