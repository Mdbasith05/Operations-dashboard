import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Operations Dashboard", layout="wide")
st.title("📊 Operations Performance Dashboard")

st.sidebar.header("Upload Operations Dataset")

uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df["Date"] = pd.to_datetime(df["Date"])

    # KPI Calculations
    total_tasks = df["Tasks_Assigned"].sum()
    completed_tasks = df["Tasks_Completed"].sum()
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    sla_compliance = (df["Completion_Time"] <= df["SLA_Target"]).mean() * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tasks", total_tasks)
    col2.metric("Completed Tasks", completed_tasks)
    col3.metric("Completion Rate (%)", f"{completion_rate:.2f}%")

    st.subheader("Department Performance")
    dept = df.groupby("Department")["Tasks_Completed"].sum().reset_index()
    fig = px.bar(dept, x="Department", y="Tasks_Completed")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Raw Data")
    st.dataframe(df)

else:
    st.info("Please upload a CSV file to view the dashboard.")