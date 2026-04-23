"""Streamlit entry point — Doctor Performance Analysis System.

Run:
    streamlit run app.py
"""
from __future__ import annotations
import io
import streamlit as st
import pandas as pd

import time
import streamlit as st

if "loaded" not in st.session_state:
    st.session_state.loaded = False

if not st.session_state.loaded:
    st.markdown("""
        <div style="
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
            flex-direction:column;
        ">
            <h1 style="
                font-size:60px;
                color:#1E3A8A;
                animation: fadeIn 1.5s ease-in-out;
            ">
                MedMetrics
            </h1>
            <p style="color:gray;">Doctor Performance Analytics</p>
        </div>

        <style>
        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }
        </style>
    """, unsafe_allow_html=True)

    time.sleep(2)
    st.session_state.loaded = True
    st.rerun()

from data_ingestion import load_dataset, validate_schema, REQUIRED_COLUMNS
from preprocessing import clean_dataset
from kpi_engine import compute_kpis, monthly_success_trend, specialization_summary
from visualization import bar_top_doctors, line_trend, radar_compare, heatmap_specialization
from sample_data import generate_mock_dataset

st.set_page_config(page_title="Doctor Performance Analysis", page_icon="🩺", layout="wide")
st.markdown("""
<style>

/* App background */
.stApp {
    background-color: #F9FAFB;
}

/* Buttons hover */
button:hover {
    border: 1px solid #3B82F6 !important;
    box-shadow: 0 0 10px rgba(59,130,246,0.3);
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: white;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #E5E7EB;
}

/* Metric hover */
[data-testid="stMetric"]:hover {
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    transform: translateY(-3px);
    transition: 0.2s;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF;
}

</style>
""", unsafe_allow_html=True)
st.title("🏥 Doctor Performance Analysis System")
st.markdown("Analyze doctor performance using KPIs like success rate, satisfaction, and efficiency.")

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

    # ---------- HEADER ----------
    st.markdown("## 🏥 Dashboard Overview")
    st.markdown("Monitor doctor performance, efficiency, and patient outcomes")
    st.markdown("---")

    # ---------- FILTER ----------
    specs = ["All"] + sorted(kpis["specialization"].unique().tolist())
    spec = st.selectbox("Filter by Specialization", specs)
    view = kpis if spec == "All" else kpis[kpis["specialization"] == spec]

    # ---------- KPI CARDS ----------
    st.markdown("### 📊 Key Metrics")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("👨‍⚕️ Doctors", len(view))
    c2.metric("✅ Success", f"{view['success_rate'].mean():.1f}%")
    c3.metric("⭐ Satisfaction", f"{view['satisfaction'].mean():.2f}/10")
    c4.metric("⏱ Avg Time", f"{view['avg_consultation'].mean():.1f} min")
    c5.metric("🔁 Readmit", f"{view['readmission_rate'].mean():.1f}%")

    st.markdown("---")

    # ---------- CHARTS ----------
    st.markdown("### 📈 Performance Insights")

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("#### 🏆 Top Performing Doctors")
        st.plotly_chart(bar_top_doctors(view), use_container_width=True)

    with col2:
        st.markdown("#### 📉 Monthly Trends")
        st.plotly_chart(line_trend(monthly_success_trend(df)), use_container_width=True)

    st.markdown("---")

    # ---------- HEATMAP ----------
    st.markdown("### 🧠 Specialization Insights")
    st.plotly_chart(heatmap_specialization(view), use_container_width=True)

    st.markdown("---")

    # ---------- TABLE ----------
    st.markdown("### 🏆 Doctor Ranking")

    show = view.copy()
    show["status"] = show["flagged"].map({True: "⚠️ Needs Attention", False: "✅ Good"})

    st.dataframe(
        show.drop(columns=["flagged"]),
        use_container_width=True
    )

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
