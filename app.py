"""Streamlit entry point — Doctor Performance Analysis System.

Run:
    streamlit run app.py
"""
from __future__ import annotations
import io
import streamlit as st
import pandas as pd

from data_ingestion import load_dataset, validate_schema, REQUIRED_COLUMNS
from preprocessing import clean_dataset
from kpi_engine import compute_kpis, monthly_success_trend, specialization_summary
from visualization import bar_top_doctors, line_trend, radar_compare, heatmap_specialization
from sample_data import generate_mock_dataset

st.set_page_config(page_title="Doctor Performance Analysis", page_icon="🩺", layout="wide")

# ---------- Sidebar ----------
st.sidebar.title("🩺 MedMetrics")
st.sidebar.caption("Doctor Performance Analysis")
section = st.sidebar.radio("Navigate", ["Upload", "Dashboard", "Compare", "Insights", "Reports"])
threshold = st.sidebar.slider("Underperformance threshold (composite)", 30, 90, 60)

# ---------- Data state ----------
if "df" not in st.session_state:
    st.session_state.df = clean_dataset(generate_mock_dataset())
    st.session_state.source = "demo"

df: pd.DataFrame = st.session_state.df
kpis = compute_kpis(df, threshold=threshold)

# ---------- UPLOAD ----------
if section == "Upload":
    st.header("Upload dataset")
    st.write("Provide a CSV/Excel with patient-level treatment records.")
    st.code(", ".join(REQUIRED_COLUMNS), language="text")

    up = st.file_uploader("CSV or Excel", type=["csv", "xlsx", "xls"])
    if up is not None:
        suffix = up.name.split(".")[-1].lower()
        raw = pd.read_csv(up) if suffix == "csv" else pd.read_excel(up)
        ok, missing = validate_schema(raw)
        if not ok:
            st.error(f"Missing required columns: {missing}")
        else:
            cleaned = clean_dataset(raw)
            st.session_state.df = cleaned
            st.session_state.source = "uploaded"
            st.success(f"Loaded {len(cleaned)} clean records (from {len(raw)} raw rows).")
            st.dataframe(cleaned.head())

    if st.button("Reset to demo data"):
        st.session_state.df = clean_dataset(generate_mock_dataset())
        st.session_state.source = "demo"
        st.rerun()

    st.info(f"Currently using **{st.session_state.source}** data — {len(df):,} records.")

# ---------- DASHBOARD ----------
elif section == "Dashboard":
    st.header("Overview")
    specs = ["All"] + sorted(kpis["specialization"].unique().tolist())
    spec = st.selectbox("Specialization", specs)
    view = kpis if spec == "All" else kpis[kpis["specialization"] == spec]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Doctors", len(view))
    c2.metric("Success rate", f"{view['success_rate'].mean():.1f}%")
    c3.metric("Satisfaction", f"{view['satisfaction'].mean():.2f}/10")
    c4.metric("Avg consult", f"{view['avg_consultation'].mean():.1f} min")
    c5.metric("Readmission", f"{view['readmission_rate'].mean():.1f}%")
    c6.metric("Diag. accuracy", f"{view['diagnosis_accuracy'].mean():.1f}%")

    left, right = st.columns(2)
    left.plotly_chart(bar_top_doctors(view), use_container_width=True)
    right.plotly_chart(line_trend(monthly_success_trend(df)), use_container_width=True)

    st.subheader("Doctor ranking")
    show = view.copy()
    show["status"] = show["flagged"].map({True: "⚠ Flagged", False: "✅ OK"})
    st.dataframe(show.drop(columns=["flagged"]), use_container_width=True)

# ---------- COMPARE ----------
elif section == "Compare":
    st.header("Side-by-side comparison")
    options = {f"{r.doctor_name} — {r.specialization}": r.doctor_id for r in kpis.itertuples()}
    keys = list(options.keys())
    a_key = st.selectbox("Doctor A", keys, index=0)
    b_key = st.selectbox("Doctor B", keys, index=min(1, len(keys) - 1))
    a_id, b_id = options[a_key], options[b_key]
    st.plotly_chart(radar_compare(kpis, a_id, b_id), use_container_width=True)
    st.dataframe(kpis[kpis["doctor_id"].isin([a_id, b_id])], use_container_width=True)

# ---------- INSIGHTS ----------
elif section == "Insights":
    st.header("Insights")
    st.plotly_chart(heatmap_specialization(kpis), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏆 Top performers")
        st.dataframe(kpis.head(5)[["doctor_name", "specialization", "composite"]],
                     use_container_width=True, hide_index=True)
    with c2:
        st.subheader("⚠ Needs attention")
        st.dataframe(kpis.tail(5)[["doctor_name", "specialization", "composite", "flagged"]]
                     .sort_values("composite"), use_container_width=True, hide_index=True)

    st.subheader("Specialization summary")
    st.dataframe(specialization_summary(kpis), use_container_width=True, hide_index=True)

# ---------- REPORTS ----------
elif section == "Reports":
    st.header("Export reports")

    csv_bytes = kpis.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download CSV summary", csv_bytes,
                       file_name="doctor_performance.csv", mime="text/csv")

    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as w:
        kpis.to_excel(w, sheet_name="KPIs", index=False)
        specialization_summary(kpis).to_excel(w, sheet_name="By specialization", index=False)
        monthly_success_trend(df).to_excel(w, sheet_name="Trend", index=False)
    st.download_button("⬇ Download Excel report", excel_buf.getvalue(),
                       file_name="doctor_performance.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
