import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="2026 Growth Tracker", page_icon="🚀", layout="wide")

# --- ASSETS ---
GIF_HIGH = "https://gifdb.com/images/high/weight-lifting-machio-naruzo-muscles-b7iwxzcmqu9iqm8v.gif"
GIF_MID = "https://gifdb.com/images/high/weight-lifting-one-piece-zoro-dumbbell-9fijwjssrinfxgsf.gif"
GIF_LOW = "https://gifdb.com/images/high/weight-lifting-nijigasaki-kasumi-nakasu-i8k4v57vhfxyaqur.gif"

AI_ROADMAP = {
    1: "Jan: Python Basics & OOP", 2: "Feb: Automation Framework",
    3: "Mar: API Testing & Reporting", 4: "Apr: LangChain & RAG",
    5: "May: RAG Project", 6: "Jun: LLM Evaluation",
    7: "Jul: AI Testing Framework", 8: "Aug: Dataset Creation",
    9: "Sep: Fine-tuning Basics", 10: "Oct: AI Agents",
    11: "Nov: Optimization", 12: "Dec: Capstone Project"
}

QUESTIONS = [
    {"key": "Workout", "icon": "💪", "color": "red", "q": "Did you WORKOUT today?", "ask_detail": "What exercise?"},
    {"key": "Code", "icon": "💻", "color": "blue", "q": "Did you CODE/AI today?", "ask_detail": "Topic studied?"},
    {"key": "Read", "icon": "📚", "color": "orange", "q": "Did you READ 10 mins?", "ask_detail": "Book/Page?"},
    {"key": "NoJunk", "icon": "🥦", "color": "green", "q": "Did you eat CLEAN?", "ask_detail": "What meal?"},
    {"key": "Connect", "icon": "🤝", "color": "pink", "q": "Did you CONNECT?", "ask_detail": "Who?"},
    {"key": "SideHustle", "icon": "🎥", "color": "violet", "q": "SIDE HUSTLE work?", "ask_detail": "Progress?"}
]

# --- CONNECT TO DB ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        conn.reset()
        return conn.read(worksheet="Logs", usecols=list(range(14)), ttl=0)
    except:
        return pd.DataFrame()

def update_data(df):
    conn.update(worksheet="Logs", data=df)

# --- HELPER: SAVE LOGIC ---
def save_partial_log(date_obj, key, val, detail):
    df = get_data()
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
    
    if not df.empty and date_obj in df["Date"].values:
        mask = df["Date"] == date_obj
        df.loc[mask, key] = val
        df.loc[mask, f"{key}_Detail"] = detail
        final_df = df
    else:
        new_row = {"Date": date_obj}
        for q in QUESTIONS:
            new_row[q["key"]] = 0
            new_row[f"{q['key']}_Detail"] = ""
        new_row["Next_Goal"] = ""
        new_row[key] = val
        new_row[f"{key}_Detail"] = detail
        new_df = pd.DataFrame([new_row])
        final_df = pd.concat([df, new_df], ignore_index=True)
    
    update_data(final_df)
    
    # Perfection Check
    today_row = final_df[final_df["Date"] == date_obj].iloc[0]
    total_done = sum([1 for q in QUESTIONS if today_row.get(q["key"], 0) == 1])
    
    if total_done == 6:
        st.balloons()
        st.toast("🏆 PERFECTION! 6/6 Habits Done!", icon="🎉")
    else:
        st.toast(f"Saved {key}! ({total_done}/6 Done)", icon="✅")
    time.sleep(1)
    st.rerun()

def save_goal(date_obj, goal_text):
    df = get_data()
    if not df.empty: df["Date"] = pd.to_datetime(df["Date"]).dt.date
    
    if not df.empty and date_obj in df["Date"].values:
        df.loc[df["Date"] == date_obj, "Next_Goal"] = goal_text
        final_df = df
    else:
        new_row = {"Date": date_obj, "Next_Goal": goal_text}
        for q in QUESTIONS: new_row[q["key"]] = 0
        final_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
    update_data(final_df)
    st.toast("Goal Committed!", icon="🔮")
    time.sleep(1)
    st.rerun()

# --- APP START ---
st.title("🚀 2026 Growth Dashboard")
current_month = date.today().month
st.markdown(f"### 🎯 Focus: **{AI_ROADMAP.get(current_month, 'Growth')}**")

# --- LOAD DATA ---
try:
    df = get_data()
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        habit_cols = [q["key"] for q in QUESTIONS]
        def clean_bool(val):
            try: return 1 if float(val) > 0 else 0
            except: return 1 if str(val).upper() in ["TRUE", "T", "YES", "ON"] else 0
        for col in habit_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0).apply(clean_bool)
except:
    st.error("DB Connection Error")
    st.stop()

today = date.today()

# --- TOP STATS & GIF ---
today_progress = 0
if not df.empty and today in df["Date"].values:
    row = df[df["Date"] == today].iloc[0]
    today_progress = sum([1 for q in QUESTIONS if clean_bool(row.get(q["key"], 0)) == 1])

if today_progress >= 4:
    current_gif = GIF_HIGH
    status_msg = f"🔥 **BEAST MODE!** ({today_progress}/6)"
elif today_progress == 3:
    current_gif = GIF_MID
    status_msg = f"⚔️ **MOMENTUM...** ({today_progress}/6)"
else:
    current_gif = GIF_LOW
    status_msg = f"🌱 **WARMING UP...** ({today_progress}/6)"

c1, c2 = st.columns([1, 4])
with c1: st.image(current_gif, use_container_width=True)
with c2:
    st.info(status_msg)
    today_goal_msg = "No goal set."
    if not df.empty:
        yest = today - timedelta(days=1)
        y_row = df[df["Date"] == yest]
        if not y_row.empty and "Next_Goal" in y_row.columns:
            g = y_row.iloc[0]["Next_Goal"]
            if pd.notna(g) and str(g).strip(): today_goal_msg = f"🔮 **Target:** {g}"
    st.write(today_goal_msg)
    with st.popover("Set Tomorrow's Goal"):
        new_g = st.text_input("One Goal:")
        if st.button("Commit"): save_goal(today, new_g)

st.divider()

# --- CONTROL CENTER ---
st.subheader("📝 Daily Control Center")
today_data = {}
if not df.empty and today in df["Date"].values:
    r = df[df["Date"] == today].iloc[0]
    for q in QUESTIONS:
        k = q["key"]
        val = clean_bool(r.get(k, 0))
        det = r.get(f"{k}_Detail", "")
        today_data[k] = {"done": val == 1, "detail": det}

cols = st.columns(3) + st.columns(3)
for idx, q in enumerate(QUESTIONS):
    key = q["key"]
    stat = today_data.get(key, {"done": False, "detail": ""})
    icon = "✅" if stat["done"] else "⬜"
    with cols[idx]:
        with st.expander(f"{icon} {key}", expanded=not stat["done"]):
            st.caption(q["q"])
            with st.form(f"f_{key}"):
                chk = st.checkbox("Done?", value=stat["done"])
                det = st.text_input(q["ask_detail"], value=str(stat["detail"]) if pd.notna(stat["detail"]) else "")
                if st.form_submit_button("Save"):
                    if chk and not det.strip(): st.error("Detail needed!")
                    else: save_partial_log(today, key, 1 if chk else 0, det)

# --- ANALYTICS ---
if not df.empty:
    st.divider()
    st.subheader("📊 Performance & Rewards")
    
    # 1. METRICS ROW
    m1, m2, m3, m4 = st.columns(4)
    this_month = df[pd.to_datetime(df["Date"]).dt.month == current_month]
    
    # WEEKLY JACKPOT LOGIC
    # Get current week data (Mon-Sat only)
    curr_week_num = today.isocalendar().week
    df["Week"] = pd.to_datetime(df["Date"]).dt.isocalendar().week
    df["DayOfWeek"] = pd.to_datetime(df["Date"]).dt.dayofweek # 0=Mon, 6=Sun
    
    this_week_df = df[(df["Week"] == curr_week_num) & (df["DayOfWeek"] != 6)]
    
    # Calculate Weekly Score
    habit_keys = [q["key"] for q in QUESTIONS]
    tasks_done = this_week_df[habit_keys].sum().sum()
    
    # Total possible so far this week (Dynamic: Today's day index + 1 * 6 habits)
    # Or Fixed: Total possible for a FULL week is 36
    # Let's use FIXED 36 to show progress towards the weekly goal
    total_possible_week = 36 
    
    weekly_pct = 0
    if total_possible_week > 0:
        weekly_pct = int((tasks_done / total_possible_week) * 100)
    
    reward_points = 0
    reward_status = "❌ Locked"
    if weekly_pct > 50:
        reward_points = int(weekly_pct) * 50
        reward_status = "🔓 UNLOCKED!"
    
    m1.metric("Weekly Progress", f"{weekly_pct}%", f"{tasks_done}/36 Tasks")
    m2.metric("Weekly Jackpot", f"{reward_points} Pts", reward_status)
    
    # LIFETIME POINTS (Simple accumulation for fun)
    total_habits_all_time = df[habit_keys].sum().sum()
    lifetime_score = int(total_habits_all_time * 10) + (reward_points if weekly_pct > 50 else 0)
    m3.metric("Lifetime Score", f"{lifetime_score}", "XP")
    
    # Discipline Score (Mon-Sat)
    work_days = this_month[pd.to_datetime(this_month["Date"]).dt.dayofweek != 6]
    if len(work_days) > 0:
        d_score = int((work_days[habit_keys].sum().sum() / (len(work_days) * 6)) * 100)
        m4.metric("Discipline (Mon-Sat)", f"{d_score}%")
    else:
        m4.metric("Discipline", "0%")

    # 2. HEATMAP
    if habit_keys:
        df["Total_Score"] = df[habit_keys].sum(axis=1)
        heat_data = df.copy()
        heat_data["Day"] = pd.to_datetime(heat_data["Date"]).dt.day_name()
        fig = px.density_heatmap(heat_data, x="Week", y="Day", z="Total_Score", nbinsx=52, color_continuous_scale="Greens")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("History"):
        st.dataframe(df.sort_values("Date", ascending=False))
