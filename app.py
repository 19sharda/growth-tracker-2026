import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="2026 Growth Tracker", page_icon="🚀", layout="wide")

# --- SESSION STATE (The Memory for the Wizard) ---
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# --- AI ROADMAP ---
AI_ROADMAP = {
    1: "Jan: Python Basics & OOP", 2: "Feb: Automation Framework",
    3: "Mar: API Testing & Reporting", 4: "Apr: LangChain & RAG",
    5: "May: RAG Project", 6: "Jun: LLM Evaluation",
    7: "Jul: AI Testing Framework", 8: "Aug: Dataset Creation",
    9: "Sep: Fine-tuning Basics", 10: "Oct: AI Agents",
    11: "Nov: Optimization", 12: "Dec: Capstone Project"
}

# --- CONNECT TO DB ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        return conn.read(worksheet="Logs", usecols=list(range(13)), ttl=0)
    except:
        return pd.DataFrame()

def update_data(df):
    conn.update(worksheet="Logs", data=df)

# --- CONFIG FOR QUESTIONS ---
# This dictionary controls the Wizard
QUESTIONS = [
    {
        "key": "Workout", "icon": "💪", "color": "red",
        "q": "Did you WORKOUT today?", 
        "ask_detail": "What exercise did you do?",
        "success_msg": "Gains secured! Muscle building..."
    },
    {
        "key": "Code", "icon": "💻", "color": "blue",
        "q": "Did you CODE or Learn AI?", 
        "ask_detail": "What topic did you study?",
        "success_msg": "Brain power increased! Leveling up..."
    },
    {
        "key": "Read", "icon": "📚", "color": "orange",
        "q": "Did you READ 10 mins?", 
        "ask_detail": "Which book and page?",
        "success_msg": "Wisdom acquired! Mind expanding..."
    },
    {
        "key": "NoJunk", "icon": "🥦", "color": "green",
        "q": "Did you eat CLEAN (No Junk)?", 
        "ask_detail": "What was your healthy meal?",
        "success_msg": "Body fueled! Health optimized..."
    },
    {
        "key": "Connect", "icon": "❤️", "color": "pink",
        "q": "Did you CONNECT with someone?", 
        "ask_detail": "Who did you call/meet?",
        "success_msg": "Bond strengthened! Heart warming..."
    },
    {
        "key": "SideHustle", "icon": "🎥", "color": "violet",
        "q": "Did you do SIDE HUSTLE work?", 
        "ask_detail": "What progress did you make?",
        "success_msg": "Empire building! Future secured..."
    }
]

# --- APP START ---
st.title("🚀 2026 Growth Dashboard")
current_month = date.today().month
st.markdown(f"### 🎯 Focus: **{AI_ROADMAP.get(current_month, 'Growth')}**")

# --- LOAD DATA ---
try:
    df = get_data()
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        # Clean Data Logic (Robust 1/0 cleaning)
        habit_cols = [q["key"] for q in QUESTIONS]
        def clean_bool(val):
            try:
                return 1 if float(val) > 0 else 0
            except:
                return 1 if str(val).upper() in ["TRUE", "T", "YES", "ON"] else 0
        for col in habit_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0).apply(clean_bool)
except Exception as e:
    st.error("DB Error")
    st.stop()

# --- WIZARD SIDEBAR LOGIC ---
with st.sidebar:
    st.header("📝 Daily Log Wizard")
    today = date.today()
    
    # PROGRESS BAR
    total_steps = len(QUESTIONS)
    # Current step index (0 is start screen, 1..6 are questions, 7 is review)
    if st.session_state.step > 0 and st.session_state.step <= total_steps:
        st.progress((st.session_state.step - 1) / total_steps)

    # --- STEP 0: START SCREEN ---
    if st.session_state.step == 0:
        if not df.empty and today in df["Date"].values:
            st.warning(f"⚠️ Log for {today} exists.")
        
        st.write("Ready to log your wins?")
        if st.button("🚀 Start Logging", type="primary", use_container_width=True):
            st.session_state.step = 1
            st.session_state.answers = {}
            st.rerun()

    # --- STEPS 1 to 6: QUESTIONS ---
    elif 1 <= st.session_state.step <= total_steps:
        q_index = st.session_state.step - 1
        current_q = QUESTIONS[q_index]
        
        st.subheader(f"{current_q['icon']} {current_q['key']}")
        st.write(f"**{current_q['q']}**")
        
        # Radio Button for Yes/No
        response = st.radio("Select:", ["No", "Yes"], index=0, key=f"radio_{q_index}")
        
        detail_input = ""
        if response == "Yes":
            detail_input = st.text_input(current_q['ask_detail'], key=f"text_{q_index}")
        
        # NAVIGATION BUTTONS
        col_back, col_next = st.columns([1, 2])
        if col_back.button("⬅️ Back"):
            st.session_state.step -= 1
            st.rerun()
            
        if col_next.button("Next ➡️", type="primary"):
            # Validation: If Yes, detail is mandatory
            if response == "Yes" and detail_input.strip() == "":
                st.error("⚠️ Please type what you did!")
            else:
                # Save answer to session
                st.session_state.answers[current_q['key']] = 1 if response == "Yes" else 0
                st.session_state.answers[f"{current_q['key']}_Detail"] = detail_input
                
                # ANIMATION IF YES
                if response == "Yes":
                    st.toast(current_q['success_msg'], icon=current_q['icon'])
                
                st.session_state.step += 1
                st.rerun()

    # --- STEP 7: REVIEW & SAVE ---
    elif st.session_state.step > total_steps:
        st.subheader("✅ Summary for Today")
        
        # Show Summary
        cnt = 0
        for q in QUESTIONS:
            key = q["key"]
            val = st.session_state.answers.get(key, 0)
            detail = st.session_state.answers.get(f"{key}_Detail", "")
            if val == 1:
                st.success(f"**{key}:** {detail}")
                cnt += 1
            else:
                st.markdown(f"❌ {key}")
        
        st.divider()
        col_edit, col_save = st.columns([1, 2])
        
        if col_edit.button("🔄 Edit"):
            st.session_state.step = 1
            st.rerun()
            
        if col_save.button("💾 Save to Cloud", type="primary"):
            # Construct DataFrame row
            row_data = {"Date": today}
            for k, v in st.session_state.answers.items():
                row_data[k] = v
            
            new_df = pd.DataFrame([row_data])
            
            # Combine
            if not df.empty:
                final_df = df[df["Date"] != today]
                final_df = pd.concat([final_df, new_df], ignore_index=True)
            else:
                final_df = new_df
                
            update_data(final_df)
            
            # CELEBRATION
            st.balloons()
            st.success("Saved Successfully!")
            time.sleep(2)
            st.session_state.step = 0 # Reset
            st.rerun()

# --- ANALYTICS DASHBOARD (Main Area) ---
if not df.empty:
    st.divider()
    
    # METRICS
    df["Month"] = pd.to_datetime(df["Date"]).dt.month
    df["Week"] = pd.to_datetime(df["Date"]).dt.isocalendar().week
    this_month = df[df["Month"] == current_month]
    
    # Calculate Connect
    curr_week = date.today().isocalendar()[1]
    connect_week = df[df["Week"] == curr_week]["Connect"].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Coding Streak", f"{int(this_month['Code'].sum())} d")
    c2.metric("Workouts", f"{int(this_month['Workout'].sum())} d")
    c3.metric("Connect (Week)", f"{int(connect_week)}/2")
    
    # Score
    days = len(this_month)
    if days > 0:
        pts = this_month[habit_cols].sum().sum()
        # Max possible points = days * 6 habits
        score = int((pts / (days * 6)) * 100)
        c4.metric("Discipline", f"{score}%")
    
    st.divider()
    
    # CHARTS
    col_chart, col_opts = st.columns([3, 1])
    with col_opts:
        c_type = st.radio("Chart:", ["Bar", "Line", "Pie"])
        t_view = st.radio("View:", ["Daily", "Weekly", "Monthly"])
        
    with col_chart:
        plot_df = df.copy()
        x_ax = "Date"
        if t_view == "Weekly": 
            plot_df = plot_df.groupby("Week")[habit_cols].sum().reset_index()
            x_ax = "Week"
        elif t_view == "Monthly":
            plot_df = plot_df.groupby("Month")[habit_cols].sum().reset_index()
            x_ax = "Month"
            
        melted = plot_df.melt(id_vars=[x_ax], var_name="Habit", value_name="Count")
        melted["Count"] = pd.to_numeric(melted["Count"], errors='coerce').fillna(0)
        melted = melted[melted["Count"] > 0]
        
        if c_type == "Bar":
            fig = px.bar(melted, x=x_ax, y="Count", color="Habit", barmode="group")
        elif c_type == "Line":
            fig = px.line(melted, x=x_ax, y="Count", color="Habit", markers=True)
        else:
            fig = px.pie(melted, values="Count", names="Habit")
            
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📂 View Detailed Journal"):
        st.dataframe(df.sort_values("Date", ascending=False))
else:
    st.info("👈 Click 'Start Daily Log' in the sidebar!")
