"""Generate a deterministic synthetic doctor-patient dataset for demos."""
from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import date, timedelta

SPECS = ["Cardiology", "Neurology", "Pediatrics", "Orthopedics", "Oncology", "General Medicine"]
NAMES = [
    "Dr. Aisha Khan", "Dr. Ben Carter", "Dr. Chen Wei", "Dr. Diana Reyes",
    "Dr. Ethan Brooks", "Dr. Fatima Noor", "Dr. Grace Lin", "Dr. Hiroshi Tanaka",
    "Dr. Ivan Petrov", "Dr. Julia Santos", "Dr. Kavita Rao", "Dr. Liam Walsh",
]


def generate_mock_dataset(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    pid = 1
    base = date(2024, 7, 1)
    for i, name in enumerate(NAMES):
        skill = 0.55 + rng.random() * 0.4
        n = int(60 + rng.integers(0, 80))
        for _ in range(n):
            r = rng.random()
            outcome = "success" if r < skill else "partial" if r < skill + 0.15 else "failure"
            sat = int(np.clip(round(skill * 10 + (rng.random() - 0.5) * 3), 1, 10))
            rows.append({
                "doctor_id": f"D{i+1:03d}",
                "doctor_name": name,
                "specialization": SPECS[i % len(SPECS)],
                "patient_id": f"P{pid:05d}",
                "treatment_outcome": outcome,
                "satisfaction_score": sat,
                "consultation_time_min": int(10 + rng.random() * 35),
                "readmitted": bool(rng.random() > skill + 0.15),
                "diagnosis_correct": bool(rng.random() < skill + 0.1),
                "date": (base + timedelta(days=int(rng.integers(0, 180)))).isoformat(),
            })
            pid += 1
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_mock_dataset()
    df.to_csv("sample_dataset.csv", index=False)
    print(f"Wrote sample_dataset.csv with {len(df)} rows")
