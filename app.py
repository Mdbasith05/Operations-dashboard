import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import datetime

# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Operations Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .main {
        background-color: #0f1117;
        color: #e8eaf0;
    }

    .stApp {
        background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 100%);
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
    }

    .metric-card {
        background: linear-gradient(135deg, #1e2235 0%, #252a3d 100%);
        border: 1px solid #2e3455;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        font-family: 'Space Grotesk', sans-serif;
        color: #7c8ef7;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #8b92b0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }

    .metric-delta {
        font-size: 0.85rem;
        margin-top: 6px;
    }

    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #c8ccdf;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #2e3455;
        font-family: 'Space Grotesk', sans-serif;
    }

    .stSidebar {
        background: #141623 !important;
    }

    .export-btn {
        background: linear-gradient(135deg, #5c6bc0, #7c8ef7);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
        cursor: pointer;
    }

    div[data-testid="stDownloadButton"] button {
        background: linear-gradient(135deg, #5c6bc0, #7c8ef7) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 12px !important;
    }

    .badge-green {
        background: #1a3a2a;
        color: #4caf8a;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .badge-red {
        background: #3a1a1a;
        color: #f87171;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ─── Color Palette ─────────────────────────────────────────────
COLORS = ["#7c8ef7", "#4caf8a", "#f6a740", "#f87171", "#a78bfa", "#38bdf8"]
CHART_THEME = dict(
    plot_bgcolor="#1e2235",
    paper_bgcolor="#1e2235",
    font_color="#c8ccdf",
    font_family="DM Sans"
)

# ─── Helper: Export to Excel ───────────────────────────────────
def export_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Operations Data")

        # KPI Summary sheet
        total_tasks = df["Tasks_Assigned"].sum()
        completed_tasks = df["Tasks_Completed"].sum()
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        sla_compliance = (df["Completion_Time"] <= df["SLA_Target"]).mean() * 100
        avg_completion = df["Completion_Time"].mean()

        kpi_df = pd.DataFrame({
            "KPI": ["Total Tasks", "Completed Tasks", "Completion Rate (%)", "SLA Compliance (%)", "Avg Completion Time"],
            "Value": [total_tasks, completed_tasks, f"{completion_rate:.2f}%", f"{sla_compliance:.2f}%", f"{avg_completion:.2f}"]
        })
        kpi_df.to_excel(writer, index=False, sheet_name="KPI Summary")

        # Department summary sheet
        dept_summary = df.groupby("Department").agg(
            Tasks_Assigned=("Tasks_Assigned", "sum"),
            Tasks_Completed=("Tasks_Completed", "sum"),
        ).reset_index()
        dept_summary["Completion_Rate_%"] = (dept_summary["Tasks_Completed"] / dept_summary["Tasks_Assigned"] * 100).round(2)
        dept_summary.to_excel(writer, index=False, sheet_name="Department Summary")

    return output.getvalue()


# ─── Helper: Generate Sample Data ──────────────────────────────
def generate_sample_data() -> pd.DataFrame:
    import numpy as np
    np.random.seed(42)
    departments = ["Operations", "Logistics", "Finance", "HR", "IT", "Sales"]
    dates = pd.date_range("2024-01-01", periods=180, freq="D")
    rows = []
    for date in dates:
        for dept in departments:
            assigned = np.random.randint(10, 50)
            completed = np.random.randint(int(assigned * 0.6), assigned + 1)
            sla_target = np.random.choice([24, 48, 72])
            completion_time = np.random.normal(sla_target * 0.9, sla_target * 0.3)
            completion_time = max(1, round(completion_time, 1))
            rows.append({
                "Date": date,
                "Department": dept,
                "Tasks_Assigned": assigned,
                "Tasks_Completed": completed,
                "SLA_Target": sla_target,
                "Completion_Time": completion_time,
            })
    return pd.DataFrame(rows)


# ─── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Dashboard Controls")
    st.markdown("---")

    uploaded_file = st.file_uploader("📂 Upload CSV File", type=["csv"])
    use_sample = st.checkbox("Use Sample Data", value=uploaded_file is None)

    st.markdown("---")
    st.markdown("### 🔍 Filters")

# ─── Load Data ─────────────────────────────────────────────────
if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)
    df_raw["Date"] = pd.to_datetime(df_raw["Date"])
elif use_sample:
    df_raw = generate_sample_data()
    st.sidebar.info("📌 Using generated sample data")
else:
    st.info("Please upload a CSV file or enable Sample Data in the sidebar.")
    st.stop()

# ─── Sidebar Filters ───────────────────────────────────────────
with st.sidebar:
    departments = ["All"] + sorted(df_raw["Department"].unique().tolist())
    selected_dept = st.selectbox("Department", departments)

    min_date = df_raw["Date"].min().date()
    max_date = df_raw["Date"].max().date()
    date_range = st.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    st.markdown("---")
    st.markdown("### 📥 Export Data")
    excel_bytes = export_excel(df_raw)
    st.download_button(
        label="⬇️ Export to Excel",
        data=excel_bytes,
        file_name=f"operations_report_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    csv_bytes = df_raw.to_csv(index=False).encode()
    st.download_button(
        label="⬇️ Export to CSV",
        data=csv_bytes,
        file_name=f"operations_data_{datetime.date.today()}.csv",
        mime="text/csv"
    )

# ─── Apply Filters ─────────────────────────────────────────────
df = df_raw.copy()
if selected_dept != "All":
    df = df[df["Department"] == selected_dept]
if len(date_range) == 2:
    df = df[(df["Date"].dt.date >= date_range[0]) & (df["Date"].dt.date <= date_range[1])]

# ─── Header ────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 10px 0 20px 0'>
    <h1 style='color:#7c8ef7; font-family:Space Grotesk; margin:0; font-size:2.2rem'>
        📊 Operations Intelligence
    </h1>
    <p style='color:#8b92b0; margin:6px 0 0 0; font-size:0.95rem'>
        Real-time performance tracking · SLA compliance · Department analytics
    </p>
</div>
""", unsafe_allow_html=True)

# ─── KPI Calculations ──────────────────────────────────────────
total_tasks = df["Tasks_Assigned"].sum()
completed_tasks = df["Tasks_Completed"].sum()
completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
sla_compliance = (df["Completion_Time"] <= df["SLA_Target"]).mean() * 100
avg_completion = df["Completion_Time"].mean()
pending_tasks = total_tasks - completed_tasks

# ─── KPI Cards ─────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

def kpi_card(col, value, label, color="#7c8ef7"):
    col.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value' style='color:{color}'>{value}</div>
        <div class='metric-label'>{label}</div>
    </div>
    """, unsafe_allow_html=True)

kpi_card(c1, f"{total_tasks:,}", "Total Tasks")
kpi_card(c2, f"{completed_tasks:,}", "Completed", "#4caf8a")
kpi_card(c3, f"{completion_rate:.1f}%", "Completion Rate", "#f6a740")
kpi_card(c4, f"{sla_compliance:.1f}%", "SLA Compliance", "#a78bfa")
kpi_card(c5, f"{avg_completion:.1f}h", "Avg Time (hrs)", "#38bdf8")

st.markdown("<br>", unsafe_allow_html=True)

# ─── Row 1: Department Bar + Trend Line ────────────────────────
col_a, col_b = st.columns([1, 1])

with col_a:
    st.markdown("<div class='section-header'>🏢 Department Performance</div>", unsafe_allow_html=True)
    dept = df.groupby("Department").agg(
        Tasks_Completed=("Tasks_Completed", "sum"),
        Tasks_Assigned=("Tasks_Assigned", "sum")
    ).reset_index()
    dept["Completion_Rate"] = (dept["Tasks_Completed"] / dept["Tasks_Assigned"] * 100).round(1)

    fig_dept = px.bar(
        dept, x="Department", y="Tasks_Completed",
        color="Completion_Rate",
        color_continuous_scale=["#f87171", "#f6a740", "#4caf8a"],
        text="Tasks_Completed"
    )
    fig_dept.update_traces(textposition="outside", textfont_size=11)
    fig_dept.update_layout(**CHART_THEME, height=320, coloraxis_showscale=False,
                           margin=dict(t=10, b=10, l=10, r=10),
                           xaxis=dict(gridcolor="#2e3455"),
                           yaxis=dict(gridcolor="#2e3455"))
    st.plotly_chart(fig_dept, use_container_width=True)

with col_b:
    st.markdown("<div class='section-header'>📈 Tasks Trend Over Time</div>", unsafe_allow_html=True)
    trend = df.groupby("Date").agg(
        Tasks_Assigned=("Tasks_Assigned", "sum"),
        Tasks_Completed=("Tasks_Completed", "sum")
    ).reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=trend["Date"], y=trend["Tasks_Assigned"],
                                   name="Assigned", line=dict(color="#7c8ef7", width=2),
                                   fill="tozeroy", fillcolor="rgba(124,142,247,0.1)"))
    fig_trend.add_trace(go.Scatter(x=trend["Date"], y=trend["Tasks_Completed"],
                                   name="Completed", line=dict(color="#4caf8a", width=2),
                                   fill="tozeroy", fillcolor="rgba(76,175,138,0.1)"))
    fig_trend.update_layout(**CHART_THEME, height=320,
                            margin=dict(t=10, b=10, l=10, r=10),
                            legend=dict(bgcolor="#1e2235", bordercolor="#2e3455"),
                            xaxis=dict(gridcolor="#2e3455"),
                            yaxis=dict(gridcolor="#2e3455"))
    st.plotly_chart(fig_trend, use_container_width=True)

# ─── Row 2: SLA + Completion Rate by Dept ──────────────────────
col_c, col_d = st.columns([1, 1])

with col_c:
    st.markdown("<div class='section-header'>🎯 SLA Compliance by Department</div>", unsafe_allow_html=True)
    sla_dept = df.copy()
    sla_dept["SLA_Met"] = sla_dept["Completion_Time"] <= sla_dept["SLA_Target"]
    sla_summary = sla_dept.groupby("Department")["SLA_Met"].mean().reset_index()
    sla_summary["SLA_Compliance_%"] = (sla_summary["SLA_Met"] * 100).round(1)

    fig_sla = px.bar(sla_summary, x="SLA_Compliance_%", y="Department",
                     orientation="h",
                     color="SLA_Compliance_%",
                     color_continuous_scale=["#f87171", "#f6a740", "#4caf8a"],
                     text="SLA_Compliance_%")
    fig_sla.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_sla.update_layout(**CHART_THEME, height=320, coloraxis_showscale=False,
                          margin=dict(t=10, b=10, l=10, r=10),
                          xaxis=dict(range=[0, 115], gridcolor="#2e3455"),
                          yaxis=dict(gridcolor="#2e3455"))
    st.plotly_chart(fig_sla, use_container_width=True)

with col_d:
    st.markdown("<div class='section-header'>🍩 Task Distribution</div>", unsafe_allow_html=True)
    pie_data = df.groupby("Department")["Tasks_Completed"].sum().reset_index()
    fig_pie = px.pie(pie_data, names="Department", values="Tasks_Completed",
                     color_discrete_sequence=COLORS, hole=0.5)
    fig_pie.update_layout(**CHART_THEME, height=320,
                          margin=dict(t=10, b=10, l=10, r=10),
                          legend=dict(bgcolor="#1e2235"))
    fig_pie.update_traces(textposition="outside", textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

# ─── Raw Data Table ────────────────────────────────────────────
st.markdown("<div class='section-header'>📋 Raw Data</div>", unsafe_allow_html=True)
st.dataframe(
    df.sort_values("Date", ascending=False).reset_index(drop=True),
    use_container_width=True,
    height=300
)

# ─── Footer ────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; color:#3d4266; margin-top:40px; font-size:0.8rem'>
    Operations Intelligence Dashboard · Built with Streamlit & Plotly
</div>
""", unsafe_allow_html=True)