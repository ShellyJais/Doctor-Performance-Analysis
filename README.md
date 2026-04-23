# Doctor Performance Analysis System

A Python/Streamlit application that ingests doctor-patient datasets, cleans them,
computes KPIs, ranks doctors with a composite score, and produces interactive
dashboards plus exportable reports.

## Files

| File | Purpose |
|---|---|
| `data_ingestion.py` | Load CSV/Excel and validate schema |
| `preprocessing.py`  | Clean, dedupe, normalize fields |
| `kpi_engine.py`     | Compute per-doctor KPIs + composite score |
| `visualization.py`  | Plotly charts (bar, line, radar, heatmap) |
| `sample_data.py`    | Deterministic synthetic dataset generator |
| `app.py`            | Streamlit UI (Upload, Dashboard, Compare, Insights, Reports) |
| `notebook.ipynb`    | Notebook walkthrough using the same modules |

## Quickstart

```bash
pip install -r requirements.txt
python sample_data.py          # creates sample_dataset.csv (optional)
streamlit run app.py
```

## Composite score

```
composite = success_rate*0.30
          + satisfaction*10*0.25
          + diagnosis_accuracy*0.25
          + (100 - readmission_rate)*0.10
          + consultation_efficiency*0.10
```

Doctors with `composite < threshold` (default 60) are flagged as underperforming.

## Required dataset columns

`doctor_id, doctor_name, specialization, patient_id, treatment_outcome,
satisfaction_score, consultation_time_min, readmitted, diagnosis_correct, date`
