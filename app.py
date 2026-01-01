import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# --- PAGE CONFIG ---
st.set_page_config(page_title="2026 Growth Tracker v2", page_icon="🚀", layout="wide")

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
    # Read data from the Google Sheet (Now 13 columns)
    # ttl=0 ensures we don't cache old data
    df = conn.read(worksheet="Logs", usecols=list(range(13)), ttl=0)
    return df

def update_data(df):
    conn.update(worksheet="Logs", data=df)

# --- HEADER SECTION ---
st.title("🚀 2026 Growth Dashboard")
current_month = date.today().month
st.markdown(f"### 🎯 Focus: **{AI_ROADMAP[current_month]}**")

# --- LOAD & CLEAN DATA ---
try:
    df = get_data()
    
    # 1. Fix Date Column
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    
    # 2. Fix Boolean/Numeric Columns (CRITICAL FIX FOR ERROR)
    # We force all habit columns to be 0 or 1.
    habit_cols = ["Workout", "Code", "Read", "NoJunk", "Connect", "SideHustle"]
    
    def clean_bool(val):
        # Convert diverse inputs (True, "TRUE", 1, "1") to simple integer 1
        if str(val).upper() in ["TRUE", "1", "T", "YES", "ON"]:
            return 1
        return 0

    for col in habit_cols:
        # Fill missing values with 0 first
        df[col] = df[col].fillna(0)
        # Apply cleaning function
        df[col] = df[col].apply(clean_bool)

except Exception as e:
    st.error(f"Data Error: {e}")
    st.stop()

# --- INPUT SECTION (SIDEBAR) ---
with st.sidebar:
    st.header("📝 Daily Log")
    today = date.today()
    
    # Check if already logged
    if not df.empty and today in df["Date"].values:
        st.warning(f"Log for {today} exists! Overwriting...")

    with st.form("daily_log"):
        st.write(f"**Date: {today}**")
        
        # 1. Workout
        c1, c2 = st.columns([1, 2])
        workout = c1.checkbox("💪 Workout")
        workout_det = c2.text_input("Exercise done?", placeholder="e.g. Legs / Yoga")
        
        # 2. Code
        c3, c4 = st.columns([1, 2])
        code = c3.checkbox("💻 Code/AI")
        code_det = c4.text_input("Topic studied?", placeholder="e.g. Python Lists")
        
        # 3. Read
        c5, c6 = st.columns([1, 2])
        read = c5.checkbox("📚 Read")
        read_det = c6.text_input("Book & Pages?", placeholder="e.g. Atomic Habits p.40")
        
        # 4. Clean Eating
        c7, c8 = st.columns([1, 2])
        nojunk = c7.checkbox("🥦 Clean Eat")
        food_det = c8.text_input("What did you eat?", placeholder="e.g. Paneer Salad")
        
        # 5. Connect (Target: 2/week)
        c9, c10 = st.columns([1, 2])
        connect = c9.checkbox("❤️ Connect")
        connect_det = c10.text_input("Who?", placeholder="e.g. Called Mom")

        # 6. Side Hustle (Sunday special usually)
        c11, c12 = st.columns([1, 2])
        sidehustle = c11.checkbox("🎥 YouTube")
        sidehustle_det = c12.text_input("Progress?", placeholder="e.g. Scripting Video #2")

        submit = st.form_submit_button("Save to Cloud ☁️")

        if submit:
            # Mandatory check
            if (workout and not workout_det) or (code and not code_det) or (read and not read_det):
                st.error("❌ Fill in the details for what you checked!")
            else:
                new_data = pd.DataFrame([{
                    "Date": today, 
                    "Workout": workout, "Workout_Detail": workout_det,
                    "Code": code, "Code_Detail": code_det,
                    "Read": read, "Read_Detail": read_det,
                    "NoJunk": nojunk, "Food_Detail": food_det,
                    "Connect": connect, "Connect_Detail": connect_det,
                    "SideHustle": sidehustle, "SideHustle_Detail": sidehustle_det
                }])
                
                # Remove old & Save
                df = df[df["Date"] != today]
                updated_df = pd.concat([df, new_data], ignore_index=True)
                update_data(updated_df)
                st.toast("Saved successfully!", icon="✅")
                st.rerun()

# --- ANALYTICS DASHBOARD ---
if not df.empty:
    st.divider()
    
    # --- METRICS LOGIC ---
    df["Month"] = pd.to_datetime(df["Date"]).dt.month
    df["Week"] = pd.to_datetime(df["Date"]).dt.isocalendar().week
    this_month = df[df["Month"] == current_month]
    
    # Connection Logic (Target: 2 per week)
    current_week_num = date.today().isocalendar()[1]
    this_week = df[df["Week"] == current_week_num]
    connect_count = this_week["Connect"].sum()
    connect_target = 2
    
    # Display Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Coding Streak", f"{this_month['Code'].sum()} Days")
    with col2: st.metric("Workouts", f"{this_month['Workout'].sum()} Days")
    with col3: st.metric("Connect (Week)", f"{connect_count} / {connect_target}")
    with col4: 
        total_days = len(this_month)
        if total_days > 0:
            score = int(((this_month["Workout"].sum() + this_month["Code"].sum()) / (total_days * 2)) * 100)
            st.metric("Discipline Score", f"{score}%")
        else:
            st.metric("Discipline Score", "0%")

    st.divider()

    # --- CHART CONTROLS ---
    c1, c2 = st.columns([1, 3])
    with c1:
        chart_type = st.selectbox("📊 Chart Type", ["Bar Chart", "Line Chart", "Pie Chart"])
        time_view = st.selectbox("📅 Time View", ["Daily Log", "Weekly Sum", "Monthly Sum"])

    with c2:
        # Prepare Data for Plotting
        plot_df = df.copy()
        
        # Aggregation Logic
        if time_view == "Weekly Sum":
            plot_df = plot_df.groupby("Week")[habit_cols].sum().reset_index()
            x_axis = "Week"
        elif time_view == "Monthly Sum":
            plot_df = plot_df.groupby("Month")[habit_cols].sum().reset_index()
            x_axis = "Month"
        else:
            x_axis = "Date"

        # Melt for plotting
        melted_df = plot_df.melt(id_vars=[x_axis], var_name="Habit", value_name="Count")
        
        # Ensure Count is numeric before filtering (The Fix)
        melted_df["Count"] = pd.to_numeric(melted_df["Count"], errors='coerce').fillna(0)
        melted_df = melted_df[melted_df["Count"] > 0]

        if chart_type == "Bar Chart":
            fig = px.bar(melted_df, x=x_axis, y="Count", color="Habit", barmode="group", title="Growth Progress")
        elif chart_type == "Line Chart":
            fig = px.line(melted_df, x=x_axis, y="Count", color="Habit", markers=True, title="Consistency Trends")
        elif chart_type == "Pie Chart":
            total_counts = melted_df.groupby("Habit")["Count"].sum().reset_index()
            fig = px.pie(total_counts, values="Count", names="Habit", title="Effort Distribution")

        st.plotly_chart(fig, use_container_width=True)

    # --- DETAILED HISTORY ---
    with st.expander("📂 View Detailed Journal"):
        st.dataframe(df.sort_values("Date", ascending=False))
        
else:
    st.info("Start logging to see your growth!")
