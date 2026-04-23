"""Plotly visualizations for the dashboard."""
from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


MED_BLUE = "#2176C4"
MED_TEAL = "#26A69A"


def bar_top_doctors(kpis: pd.DataFrame, n: int = 10) -> go.Figure:
    top = kpis.head(n)
    fig = px.bar(
        top, x="composite", y="doctor_name", orientation="h",
        color="composite", color_continuous_scale="Blues",
        labels={"composite": "Composite score", "doctor_name": ""},
        title=f"Top {n} doctors by composite score",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False, height=420)
    return fig


def line_trend(trend: pd.DataFrame) -> go.Figure:
    fig = px.line(
        trend, x="month", y="success_rate", markers=True,
        title="Monthly treatment success rate (%)",
    )
    fig.update_traces(line_color=MED_TEAL, line_width=3)
    fig.update_layout(yaxis_range=[0, 100], height=380)
    return fig


def radar_compare(kpis: pd.DataFrame, doctor_a: str, doctor_b: str) -> go.Figure:
    a = kpis.loc[kpis["doctor_id"] == doctor_a].iloc[0]
    b = kpis.loc[kpis["doctor_id"] == doctor_b].iloc[0]

    def consult_score(m):
        return max(0.0, 100.0 - max(0.0, m - 15.0) * 2.0)

    metrics = ["Success", "Satisfaction", "Diagnosis", "Low readmit", "Consult eff."]
    va = [a.success_rate, a.satisfaction * 10, a.diagnosis_accuracy,
          100 - a.readmission_rate, consult_score(a.avg_consultation)]
    vb = [b.success_rate, b.satisfaction * 10, b.diagnosis_accuracy,
          100 - b.readmission_rate, consult_score(b.avg_consultation)]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=va + [va[0]], theta=metrics + [metrics[0]],
                                  fill="toself", name=a.doctor_name, line_color=MED_BLUE))
    fig.add_trace(go.Scatterpolar(r=vb + [vb[0]], theta=metrics + [metrics[0]],
                                  fill="toself", name=b.doctor_name, line_color=MED_TEAL))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])),
                      title=f"{a.doctor_name} vs {b.doctor_name}", height=480)
    return fig


def heatmap_specialization(kpis: pd.DataFrame) -> go.Figure:
    df = kpis.copy()
    df["low_readmit"] = 100 - df["readmission_rate"]
    df["satisfaction_100"] = df["satisfaction"] * 10
    pivot = df.groupby("specialization")[
        ["success_rate", "satisfaction_100", "diagnosis_accuracy", "low_readmit"]
    ].mean().round(1)
    pivot.columns = ["Success", "Satisfaction", "Diagnosis", "Low readmit"]
    fig = px.imshow(
        pivot, text_auto=True, aspect="auto",
        color_continuous_scale="RdYlGn", zmin=0, zmax=100,
        title="Specialization performance heatmap",
    )
    fig.update_layout(height=380)
    return fig
