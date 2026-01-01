import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# --- PAGE CONFIG ---
st.set_page_config(page_title="2026 Growth Tracker", page_icon="🚀", layout="wide")

# --- AI ROADMAP DATA ---
AI_ROADMAP = {
    1: "Jan: Python Basics & OOP", 2: "Feb: Automation Framework",
    3: "Mar: API Testing & Reporting", 4: "Apr: LangChain & RAG",
    5: "May: RAG Project", 6: "Jun: LLM Evaluation",
    7: "Jul: AI Testing Framework", 8: "Aug: Dataset Creation",
    9: "Sep: Fine-tuning Basics", 10: "Oct: AI Agents",
    11: "Nov: Optimization", 12: "Dec: Capstone Project"
}

# --- CONNECT TO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)


def get_data():
    # Read data from the Google Sheet
    df = conn.read(worksheet="Logs", usecols=list(range(7)), ttl=5)
    return df


def update_data(df):
    # Update the Google Sheet
    conn.update(worksheet="Logs", data=df)


# --- HEADER SECTION ---
st.title("🚀 2026 Growth Dashboard")
current_month = date.today().month
st.markdown(f"### 🎯 Focus: **{AI_ROADMAP[current_month]}**")

# --- LOAD DATA ---
try:
    df = get_data()
    # Ensure Date column is datetime
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
except Exception as e:
    st.error("Could not connect to Database. Please check secrets.")
    st.stop()

# --- INPUT SECTION (SIDEBAR) ---
with st.sidebar:
    st.header("📝 Daily Log")
    today = date.today()

    # Check if already logged
    if not df.empty and today in df["Date"].values:
        st.success(f"Log for {today} exists! Updating...")
        # (Logic to pre-fill would go here, simplified for reliability)

    with st.form("daily_log"):
        st.write(f"**Date: {today}**")
        workout = st.checkbox("💪 Workout (30m)")
        code = st.checkbox("💻 Code/AI (45m)")
        read = st.checkbox("📚 Read (10m)")
        nojunk = st.checkbox("🥦 Clean Eating")
        connect = st.checkbox("❤️ Connect")
        notes = st.text_input("💡 Notes / Sunday Project")

        submit = st.form_submit_button("Save to Cloud ☁️")

        if submit:
            new_data = pd.DataFrame([{
                "Date": today, "Workout": workout, "Code": code,
                "Read": read, "NoJunk": nojunk, "Connect": connect, "Notes": notes
            }])

            # Remove old entry for today if exists to avoid duplicates
            df = df[df["Date"] != today]
            updated_df = pd.concat([df, new_data], ignore_index=True)
            update_data(updated_df)
            st.toast("Saved successfully!", icon="✅")
            st.rerun()

# --- ANALYTICS DASHBOARD ---
if not df.empty:
    # Prepare Data
    df["Month"] = pd.to_datetime(df["Date"]).dt.month
    this_month_df = df[df["Month"] == current_month]

    # 1. TOP METRICS
    col1, col2, col3, col4 = st.columns(4)
    total_days = len(this_month_df)
    consistency = int((total_days / date.today().day) * 100) if date.today().day > 0 else 0

    with col1:
        st.metric("Days Logged", f"{total_days}")
    with col2:
        st.metric("Consistency", f"{consistency}%")
    with col3:
        code_days = this_month_df["Code"].sum()
        st.metric("Coding Streak", f"{code_days} Days")
    with col4:
        # Reward Calculator
        points = this_month_df[["Workout", "Code", "Read", "NoJunk", "Connect"]].sum().sum()
        max_points = total_days * 5
        score = int((points / max_points) * 100) if max_points > 0 else 0
        st.metric("Reward Score", f"{score}%")

    st.divider()

    # 2. DYNAMIC CHARTS
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("📈 Habit Consistency Trend")
        # melt dataframe for chart
        chart_data = this_month_df.melt(id_vars=["Date"], value_vars=["Workout", "Code", "Read", "NoJunk", "Connect"])
        chart_data = chart_data[chart_data["value"] == True]  # Only show completed

        fig = px.scatter(chart_data, x="Date", y="variable", color="variable",
                         title="Daily Habit Hits", height=300)
        fig.update_layout(xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("🏆 Monthly Breakdown")
        sums = this_month_df[["Workout", "Code", "Read", "NoJunk", "Connect"]].sum()
        fig2 = px.pie(values=sums, names=sums.index, hole=0.4)
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # 3. DATA VIEW
    with st.expander("📂 View Full History"):
        st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)

else:
    st.info("Start logging your days to see analytics!")