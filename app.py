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

# --- FULL YEAR ROADMAP ---
AI_ROADMAP = {
    1: {"topic": "Python Basics & OOP", "link": "https://www.learnpython.org/"},
    2: {"topic": "Automation Framework", "link": "https://testautomationuniversity.applitools.com/"},
    3: {"topic": "API Testing & Reporting", "link": "https://www.postman.com/api-platform/api-testing/"},
    4: {"topic": "LangChain & RAG", "link": "https://python.langchain.com/docs/get_started/introduction"},
    5: {"topic": "RAG Project", "link": "https://www.youtube.com/results?search_query=rag+project+python"},
    6: {"topic": "LLM Evaluation", "link": "https://docs.smith.langchain.com/"},
    7: {"topic": "AI Testing Framework", "link": "https://github.com/microsoft/promptflow"},
    8: {"topic": "Dataset Creation", "link": "https://huggingface.co/docs/datasets/index"},
    9: {"topic": "Fine-tuning Basics", "link": "https://www.philschmid.de/fine-tune-llms-in-2024-with-trl"},
    10: {"topic": "AI Agents", "link": "https://www.deeplearning.ai/short-courses/ai-agents-in-langchain/"},
    11: {"topic": "Optimization", "link": "https://huggingface.co/docs/optimum/index"},
    12: {"topic": "Capstone Project", "link": "https://github.com/"}
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
        # Fetch 15 columns (Date + 12 Habit Cols + Next_Goal + Reflection)
        return conn.read(worksheet="Logs", usecols=list(range(15)), ttl=0)
    except:
        return pd.DataFrame()

# --- GET SCHEDULE ---
def get_schedule():
    try:
        df_schedule = conn.read(worksheet="Schedule", usecols=[0, 1], ttl=0)
        df_schedule.columns = ["Date", "Task"]
        df_schedule["Date"] = pd.to_datetime(df_schedule["Date"]).dt.date
        return df_schedule
    except:
        return pd.DataFrame()

def update_data(df):
    conn.update(worksheet="Logs", data=df)

# --- HELPER: SAVE LOGIC ---
def save_partial_log(date_obj, key, val, detail):
    df = get_data()
    if not df.empty: df["Date"] = pd.to_datetime(df["Date"]).dt.date
    
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
        new_row["Reflection"] = ""
        new_row[key] = val
        new_row[f"{key}_Detail"] = detail
        new_df = pd.DataFrame([new_row])
        final_df = pd.concat([df, new_df], ignore_index=True)
    
    update_data(final_df)
    
    today_row = final_df[final_df["Date"] == date_obj].iloc[0]
    total_done = sum([1 for q in QUESTIONS if today_row.get(q["key"], 0) == 1])
    
    if total_done == 6:
        st.balloons()
        st.toast("🏆 PERFECTION! 6/6 Habits Done!", icon="🎉")
    else:
        st.toast(f"Saved {key}! ({total_done}/6 Done)", icon="✅")
    time.sleep(1)
    st.rerun()

def save_generic_text(date_obj, col_name, text):
    df = get_data()
    if not df.empty: df["Date"] = pd.to_datetime(df["Date"]).dt.date
    
    if not df.empty and date_obj in df["Date"].values:
        df.loc[df["Date"] == date_obj, col_name] = text
        final_df = df
    else:
        new_row = {"Date": date_obj, col_name: text}
        for q in QUESTIONS: new_row[q["key"]] = 0
        final_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
    update_data(final_df)
    st.toast("Saved!", icon="💾")
    time.sleep(1)
    st.rerun()

# --- APP START ---
today = date.today()
current_month = today.month

# STREAK CALCULATION
df = get_data()
streak = 0
if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df = df.sort_values("Date", ascending=False)
    habit_keys = [q["key"] for q in QUESTIONS if q["key"] in df.columns]
    df["Any_Done"] = df[habit_keys].sum(axis=1) > 0
    active_dates = df[df["Any_Done"]]["Date"].unique()
    check_date = today
    if check_date not in active_dates: check_date = today - timedelta(days=1)
    while check_date in active_dates:
        streak += 1
        check_date -= timedelta(days=1)

# HEADER
c_title, c_streak = st.columns([3, 1])
with c_title:
    st.title("🚀 2026 Growth Tracker")
with c_streak:
    st.metric("Current Streak", f"🔥 {streak} Days")

# --- 🧠 SMART MENTOR ---
schedule_df = get_schedule()
todays_task = "No specific task assigned."
task_found = False

if not schedule_df.empty:
    task_row = schedule_df[schedule_df["Date"] == today]
    if not task_row.empty:
        todays_task = task_row.iloc[0]["Task"]
        task_found = True

if task_found:
    st.info(f"📅 **TODAY'S MISSION:** {todays_task}")

with st.expander("🗺️ View Full AI Roadmap (Click to Expand)"):
    st.markdown("### 📅 Yearly Plan")
    for m in range(1, 13):
        data = AI_ROADMAP.get(m, {"topic": "TBD", "link": "#"})
        prefix = "👉" if m == current_month else "🔹"
        style = "**" if m == current_month else ""
        st.markdown(f"{prefix} {style}Month {m}: [{data['topic']}]({data['link']}){style}")

# --- TOP STATS & GIF ---
today_progress = 0
today_reflection = ""
if not df.empty and today in df["Date"].values:
    row = df[df["Date"] == today].iloc[0]
    def clean_bool(val):
        try: return 1 if float(val) > 0 else 0
        except: return 1 if str(val).upper() in ["TRUE", "T", "YES", "ON"] else 0
    today_progress = sum([1 for q in QUESTIONS if clean_bool(row.get(q["key"], 0)) == 1])
    today_reflection = row.get("Reflection", "") if pd.notna(row.get("Reflection", "")) else ""

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
    st.success(status_msg)
    cg1, cg2 = st.columns(2)
    today_goal_msg = "No goal set."
    if not df.empty:
        yest = today - timedelta(days=1)
        y_row = df[df["Date"] == yest]
        if not y_row.empty and "Next_Goal" in y_row.columns:
            g = y_row.iloc[0]["Next_Goal"]
            if pd.notna(g) and str(g).strip(): today_goal_msg = f"🔮 **Target:** {g}"
    
    with cg1:
        st.write(today_goal_msg)
        with st.popover("Set Tomorrow's Goal"):
            new_g = st.text_input("One Goal:")
            if st.button("Commit Goal"): save_generic_text(today, "Next_Goal", new_g)
    with cg2:
        if today_reflection: st.caption(f"📝 {today_reflection}")
        else: st.caption("📝 No reflection yet.")
        with st.popover("Add Note"):
            new_r = st.text_area("Note:", value=today_reflection)
            if st.button("Save Note"): save_generic_text(today, "Reflection", new_r)

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
            if key == "Code" and task_found:
                st.info(f"🎯 **Target:** {todays_task}")
                if not stat["detail"]:
                    stat["detail"] = f"Studied: {todays_task}"
            
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
    m1, m2, m3, m4 = st.columns(4)
    this_month = df[pd.to_datetime(df["Date"]).dt.month == current_month]
    
    # 1. PREP DATA FOR CALCS
    df["Date_Obj"] = pd.to_datetime(df["Date"])
    df["Week_Num"] = df["Date_Obj"].dt.isocalendar().week
    df["Year"] = df["Date_Obj"].dt.isocalendar().year
    df["DayOfWeek"] = df["Date_Obj"].dt.dayofweek 
    
    daily_habits = ["Workout", "Code", "Read", "NoJunk", "SideHustle"]
    weekly_habit = "Connect"
    
    # 2. CURRENT WEEK STATUS
    curr_week = today.isocalendar().week
    curr_year = today.isocalendar().year
    
    this_week_df = df[(df["Week_Num"] == curr_week) & (df["Year"] == curr_year) & (df["DayOfWeek"] != 6)]
    
    cur_daily = this_week_df[daily_habits].sum().sum()
    cur_connect = 1 if this_week_df[weekly_habit].sum() >= 1 else 0
    cur_total = cur_daily + cur_connect
    cur_possible = 31
    
    cur_pct = 0
    if cur_possible > 0: cur_pct = int((cur_total / cur_possible) * 100)
    
    cur_reward = 0
    if cur_pct > 50:
        cur_reward = int(cur_pct) * 5
        reward_status = "🔓 UNLOCKED!"
        delta_color = "normal"
    else:
        reward_status = "❌ Locked"
        delta_color = "off"

    today_idx = today.weekday()
    if today_idx == 6: days_msg = "Week Over"
    else: days_msg = f"⏳ {5 - today_idx} Days Left"

    # 3. HISTORICAL JACKPOT CALCULATION
    history_groups = df[df["DayOfWeek"] != 6].groupby(["Year", "Week_Num"])
    total_historical_jackpot = 0
    history_log = [] # To store list of wins
    
    for (h_year, h_week), group in history_groups:
        h_daily = group[daily_habits].sum().sum()
        h_connect = 1 if group[weekly_habit].sum() >= 1 else 0
        h_total = h_daily + h_connect
        h_pct = int((h_total / 31) * 100)
        
        pts = 0
        status = "❌ Missed"
        if h_pct > 50:
            pts = h_pct * 5
            total_historical_jackpot += pts
            status = "🏆 WON"
            
        history_log.append({
            "Week": f"{h_year}-W{h_week}",
            "Tasks Done": h_total,
            "Completion": f"{h_pct}%",
            "Points": pts,
            "Status": status
        })

    raw_xp = df[daily_habits + [weekly_habit]].sum().sum() * 10
    final_lifetime_score = raw_xp + total_historical_jackpot
    
    # 4. METRICS
    m1.metric("Weekly Progress", f"{cur_pct}%", f"{int(cur_total)}/31 Tasks")
    m2.metric("Weekly Jackpot", f"{cur_reward} Pts", f"{reward_status} | {days_msg}", delta_color=delta_color)
    m3.metric("Lifetime Score", f"{final_lifetime_score}", "XP (Includes History)")
    
    work_days = this_month[df["Date_Obj"].dt.dayofweek != 6]
    if len(work_days) > 0:
        d_score = int((work_days[daily_habits].sum().sum() / (len(work_days) * 5)) * 100)
        m4.metric("Discipline (Mon-Sat)", f"{d_score}%")
    else: m4.metric("Discipline", "0%")

    # --- TABS FOR VISUALS ---
    st.divider()
    st.subheader("📈 Trends & Consistency")
    
    tab1, tab2, tab3 = st.tabs(["📊 Charts", "🔥 Heatmap", "🏆 Jackpot Ledger"])
    
    plot_df = df.copy()
    all_keys = daily_habits + [weekly_habit]
    if all_keys: plot_df["Total_Score"] = plot_df[all_keys].sum(axis=1)

    with tab1:
        view_mode = st.radio("View:", ["Daily Trend", "Weekly Progress", "Monthly Summary"], horizontal=True)
        if view_mode == "Daily Trend":
            fig_chart = px.bar(plot_df, x="Date", y="Total_Score", color="Total_Score", color_continuous_scale="Blues")
        elif view_mode == "Weekly Progress":
            weekly_df = plot_df.groupby("Week_Num")["Total_Score"].sum().reset_index()
            fig_chart = px.bar(weekly_df, x="Week_Num", y="Total_Score", color="Total_Score", color_continuous_scale="Greens", text="Total_Score")
        elif view_mode == "Monthly Summary":
            plot_df["Month_Name"] = plot_df["Date_Obj"].dt.month_name()
            plot_df["Month_Idx"] = plot_df["Date_Obj"].dt.month
            monthly_df = plot_df.groupby(["Month_Name", "Month_Idx"])["Total_Score"].sum().reset_index().sort_values("Month_Idx")
            fig_chart = px.bar(monthly_df, x="Month_Name", y="Total_Score", color="Total_Score", color_continuous_scale="Reds", text="Total_Score")
        st.plotly_chart(fig_chart, use_container_width=True)

    with tab2:
        heat_data = plot_df.copy()
        heat_data["Day"] = heat_data["Date_Obj"].dt.day_name()
        fig_heat = px.density_heatmap(
            heat_data, x="Week_Num", y="Day", z="Total_Score", nbinsx=52, 
            color_continuous_scale="Greens",
            category_orders={"Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
    with tab3:
        st.caption("This ledger shows every week you competed.")
        if history_log:
            hist_df = pd.DataFrame(history_log).sort_values("Week", ascending=False)
            st.dataframe(hist_df, use_container_width=True)
        else:
            st.info("No history yet. Log your first week!")

    with st.expander("🔐 View Raw Data (PIN Required)"):
        pin = st.text_input("Enter PIN:", type="password", key="history_pin")
        if pin == "1234":
            st.dataframe(df.sort_values("Date", ascending=False))
        elif pin:
            st.error("🔒 Incorrect PIN")
