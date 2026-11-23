import os

import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=10000)  # refresh every 30 seconds
st.set_page_config(page_title="Palm Pro Dashboard", layout="wide")

# "http://backend:8000/events/latest" only resolves inside docker compose
# (Docker's internal DNS). Anywhere else - Azure, Railway, etc. - the real
# backend URL has to come in via env var.
API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000/events/latest")

# -----------------------
# DATA LOADING
# -----------------------
@st.cache_data(ttl=10)
def load_data():
    try:
        res = requests.get(API_URL, timeout=5)
        res.raise_for_status()

        data = res.json()

        if not data:
            return pd.DataFrame()

        return pd.DataFrame(data)

    except requests.RequestException as e:
        st.error(f"Backend unavailable: {e}")
        return pd.DataFrame()

df = load_data()
if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"])

if df.empty or "risk_score" not in df.columns:
    st.warning("No data yet — waiting for events...")
    st.stop()
# -----------------------
# HEADER
# -----------------------
st.title("📊 Palm Pro – Real-Time Sensor Intelligence Dashboard")

st.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

# -----------------------
# KPIs (TOP METRICS)
# -----------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Events", len(df))

with col2:
    st.metric("Machines", df["machine_id"].nunique())

with col3:
    st.metric("Avg Risk", f"{df['risk_score'].mean():.2f}")

with col4:
    st.metric("Critical", len(df[df["risk_score"] > 0.7]))

if "optimal_temperature" in df.columns:
    col5, col6 = st.columns(2)

    with col5:
        st.metric("Avg Optimal Temp (°C)", f"{df['optimal_temperature'].mean():.1f}")

    with col6:
        needs_adjustment = len(df[df["temperature_action"] != "MAINTAIN"])
        st.metric("Needs Temp Adjustment", needs_adjustment)

# -----------------------
# RISK DISTRIBUTION
# -----------------------
st.subheader("📈 Risk Score Distribution")

fig = px.histogram(
    df,
    x="risk_score",
    nbins=20,
    title="Distribution of Machine Risk"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------
# AVERAGE RISK OVER TIME
# -----------------------
st.subheader("📈 Average Risk Over Time")
risk_over_time = df.sort_values("timestamp")

fig = px.line(
    risk_over_time,
    x="timestamp",
    y="risk_score",
    color="machine_id",
    markers=True,
    title="Machine Risk Over Time"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------
# TEMPERATURE ADVISORY
# -----------------------
if "optimal_temperature" in df.columns:
    st.subheader("🌡️ Sterilizer Temperature: Actual vs. Optimal")

    temp_over_time = df.sort_values("timestamp")

    fig_temp = px.line(
        temp_over_time,
        x="timestamp",
        y=["temperature", "optimal_temperature"],
        facet_col="machine_id",
        markers=True,
        title="Actual Temperature vs. Recommended Optimal Temperature",
    )

    st.plotly_chart(fig_temp, use_container_width=True)

    st.subheader("🎯 Temperature Action Breakdown")

    action_counts = df["temperature_action"].value_counts().reset_index()
    action_counts.columns = ["action", "count"]

    fig_action = px.pie(
        action_counts,
        names="action",
        values="count",
        title="Recommended Actions Across Readings",
    )

    st.plotly_chart(fig_action, use_container_width=True)

# -----------------------
# MACHINE STATUS VIEW
# -----------------------
st.subheader("🟢 Machine Health Overview")

if "status" not in df.columns:
    df["status"] = df["risk_score"].apply(
        lambda x: "CRITICAL" if x > 0.8 else ("WARNING" if x > 0.5 else "OK")
    )

status_counts = df["status"].value_counts().reset_index()
status_counts.columns = ["status", "count"]

fig2 = px.pie(
    status_counts,
    names="status",
    values="count",
    title="System Health Breakdown"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------
# LIVE EVENT TABLE
# -----------------------
st.subheader("📡 Live Sensor Feed")

# st.dataframe(
#     df.sort_values(by="risk_score", ascending=False),
#     use_container_width=True
# )

feed_columns = [
    "machine_id",
    "temperature",
    "vibration",
    "pressure",
    "risk_score",
    "status",
]

if "optimal_temperature" in df.columns:
    feed_columns += ["optimal_temperature", "temperature_action"]

feed_columns.append("timestamp")

st.dataframe(
    df[feed_columns].sort_values("timestamp", ascending=False),
    use_container_width=True,
)

# -----------------------
# ALERT PANEL
# -----------------------
st.subheader("🚨 Active Alerts")

alerts = df[df["risk_score"] > 0.7]

if len(alerts) == 0:
    st.success("No active alerts 🎉 System stable")
else:
    st.error(f"{len(alerts)} high-risk events detected!")

    st.dataframe(alerts)

# -----------------------
# TEMPERATURE ALERT PANEL
# -----------------------
if "optimal_temperature" in df.columns:
    st.subheader("🌡️ Temperature Alerts")

    temp_alerts = df[df["temperature_action"] != "MAINTAIN"]

    if len(temp_alerts) == 0:
        st.success("All sterilizers within optimal range 🎉")
    else:
        st.warning(f"{len(temp_alerts)} readings need a temperature adjustment!")

        st.dataframe(
            temp_alerts[
                [
                    "machine_id",
                    "temperature",
                    "optimal_temperature",
                    "temperature_action",
                    "timestamp",
                ]
            ]
        )