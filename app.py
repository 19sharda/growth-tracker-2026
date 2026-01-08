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

# --- IST TIMEZONE CALCULATOR ---
def get_ist_date():
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return ist_now.date()

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        conn.reset()
        # Fetch 16 columns (A-P)
        return conn.read(worksheet="Logs", usecols=list(range(16)), ttl=0)
    except:
        return pd.DataFrame()

def get_schedule():
    try:
        df_schedule = conn.read(worksheet="Schedule", usecols=[0, 1], ttl=0)
        df_schedule.columns = ["Date", "Task"]
        df_schedule["Date"] = pd.to_datetime(df_schedule["Date"]).dt.date
        return df_schedule
    except:
        return pd.DataFrame()

# --- CHECKLIST FUNCTIONS ---
def get_checklist():
    try:
        return conn.read(worksheet="Checklist", usecols=[0, 1, 2], ttl=0)
    except:
        return pd.DataFrame(columns=["Task", "Tag", "Status"])

def add_checklist_item(task, tag):
    df = get_checklist()
    new_row = pd.DataFrame([{"Task": task, "Tag": tag, "Status": 0}])
    updated_df = pd.concat([df, new_row], ignore_index=True)
    conn.update(worksheet="Checklist", data=updated_df)
    st.toast(f"Added: {task}", icon="📌")
    time.sleep(1)
    st.rerun()

def toggle_checklist_item(index, new_status):
    df = get_checklist()
    df.at[index, "Status"] = 1 if new_status else 0
    conn.update(worksheet="Checklist", data=df)
    st.rerun()

def delete_checklist_item(index):
    df = get_checklist()
    df = df.drop(index).reset_index(drop=True)
    conn.update(worksheet="Checklist", data=df)
    st.rerun()

def update_data(df):
    conn.update(worksheet="Logs", data=df)

# --- SAVE LOGIC ---
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
        new_row["Weekly_Retro"] = ""
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
today = get_ist_date()
current_month = today.month
df = get_data()

# 1. STREAK
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

# 2. HEADER
c_title, c_streak = st.columns([3, 1])
with c_title:
    st.title("🚀 2026 Growth Tracker")
    st.caption(f"📅 {today.strftime('%A, %d %B %Y')} (IST)")
with c_streak:
    st.metric("Current Streak", f"🔥 {streak} Days")

# 3. SMART MENTOR
schedule_df = get_schedule()
todays_task = "No specific task assigned."
task_found = False
if not schedule_df.empty:
    task_row = schedule_df[schedule_df["Date"] == today]
    if not task_row.empty:
        todays_task = task_row.iloc[0]["Task"]
        task_found = True

if task_found: st.info(f"📅 **TODAY'S MISSION:** {todays_task}")

with st.expander("🗺️ View Full AI Roadmap (Click to Expand)", expanded=False):
    st.markdown("### 📅 Yearly Plan")
    for m in range(1, 13):
        data = AI_ROADMAP.get(m, {"topic": "TBD", "link": "#"})
        prefix = "👉" if m == current_month else "🔹"
        style = "**" if m == current_month else ""
        st.markdown(f"{prefix} {style}Month {m}: [{data['topic']}]({data['link']}){style}")

# 4. STATUS & GIF
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

# 5. CONTROL CENTER (DAILY HABITS)
st.subheader("📝 Daily Control Center")
# NOTE: Removed outer st.expander to allow inner items to be expanders
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
        # RESTORED: These are now Expanders again!
        with st.expander(f"{icon} {key}", expanded=not stat["done"]):
            if key == "Code" and task_found:
                st.info(f"🎯 **Target:** {todays_task}")
                if not stat["detail"]: stat["detail"] = f"Studied: {todays_task}"
            
            st.caption(q["q"])
            with st.form(f"f_{key}"):
                chk = st.checkbox("Done?", value=stat["done"])
                det = st.text_input(q["ask_detail"], value=str(stat["detail"]) if pd.notna(stat["detail"]) else "")
                if st.form_submit_button("Save"):
                    if chk and not det.strip(): st.error("Detail needed!")
                    else: save_partial_log(today, key, 1 if chk else 0, det)

st.divider()

# --- DYNAMIC CHECKLIST (Main Section is Expander) ---
with st.expander("📌 Dynamic Checklist (Click to Open)", expanded=False):
    col_check_1, col_check_2 = st.columns([1, 2])

    with col_check_1:
        with st.form("add_checklist_form"):
            st.markdown("**Add New Task**")
            new_task_name = st.text_input("Task Name", placeholder="e.g., Pay Rent, Complete Module 4")
            new_task_tag = st.selectbox("Tag", ["Weekly", "Monthly", "One-off", "Urgent"])
            if st.form_submit_button("Add Task"):
                if new_task_name:
                    add_checklist_item(new_task_name, new_task_tag)
                else:
                    st.error("Task name required!")

    with col_check_2:
        checklist_df = get_checklist()
        if not checklist_df.empty:
            pending = checklist_df[checklist_df["Status"] == 0]
            if not pending.empty:
                st.markdown(f"**Pending Tasks ({len(pending)})**")
                for i, row in pending.iterrows():
                    c1, c2, c3 = st.columns([0.1, 0.7, 0.2])
                    with c1:
                        if st.button("✅", key=f"done_{i}"):
                            toggle_checklist_item(i, True)
                    with c2: st.write(f"**{row['Task']}**")
                    with c3: st.caption(f"_{row['Tag']}_")
                    st.divider()
            else:
                st.info("🎉 All caught up! No pending tasks.")
                
            with st.popover("View Completed Tasks"):
                done = checklist_df[checklist_df["Status"] == 1]
                if not done.empty:
                    for i, row in done.iterrows():
                        c1, c2 = st.columns([0.8, 0.2])
                        with c1: st.write(f"~~{row['Task']}~~")
                        with c2: 
                            if st.button("🗑️", key=f"del_{i}"):
                                delete_checklist_item(i)
                else:
                    st.caption("No completed tasks yet.")
        else:
            st.info("Start by adding a Weekly or Monthly task on the left.")

# 6. ANALYTICS (Main Section is Expander)
if not df.empty:
    st.divider()
    with st.expander("📊 Analytics & History (Click to Open)", expanded=False):
        
        df["Date_Obj"] = pd.to_datetime(df["Date"])
        df["Week_Num"] = df["Date_Obj"].dt.isocalendar().week
        df["Year"] = df["Date_Obj"].dt.isocalendar().year
        
        daily_habits = ["Workout", "Code", "Read", "NoJunk", "SideHustle"]
        weekly_habit = "Connect"
        
        curr_week = today.isocalendar().week
        curr_year = today.isocalendar().year
        this_week_df = df[(df["Week_Num"] == curr_week) & (df["Year"] == curr_year)]
        
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

        habit_counts = this_week_df[daily_habits].sum().sort_values()
        missed_habits = habit_counts.head(2).index.tolist()
        missed_msg = ", ".join(missed_habits) if missed_habits else "None! (Great Job)"

        history_groups = df.groupby(["Year", "Week_Num"])
        total_historical_jackpot = 0
        history_log = [] 
        
        for (h_year, h_week), group in history_groups:
            h_daily = group[daily_habits].sum().sum()
            h_connect = 1 if group[weekly_habit].sum() >= 1 else 0
            h_total = h_daily + h_connect
            h_pct = int((h_total / 31) * 100)
            
            retro_note = ""
            if "Weekly_Retro" in group.columns:
                retro_list = group[group["Weekly_Retro"].notna() & (group["Weekly_Retro"] != "")]["Weekly_Retro"].tolist()
                if retro_list: retro_note = retro_list[-1]
            
            pts = 0
            status = "❌ Missed"
            if h_pct > 50:
                pts = h_pct * 5
                total_historical_jackpot += pts
                status = "🏆 WON"
                
            history_log.append({
                "Week": f"{h_year}-W{h_week}",
                "Tasks Done": int(h_total),
                "Completion": f"{h_pct}%",
                "Points": pts,
                "Status": status,
                "Retrospective": retro_note
            })

        raw_xp = df[daily_habits + [weekly_habit]].sum().sum() * 10
        final_lifetime_score = raw_xp + total_historical_jackpot
        d_score = 0
        if len(this_week_df) > 0:
            total_daily_slots = len(this_week_df) * 5
            if total_daily_slots > 0: d_score = int((cur_daily / total_daily_slots) * 100)

        m1, m2 = st.columns(2)
        m3, m4 = st.columns(2)
        m1.metric("Weekly Progress", f"{cur_pct}%", f"{int(cur_total)}/31 Tasks")
        m2.metric("Weekly Jackpot", f"{cur_reward} Pts", f"{reward_status} | {days_msg}", delta_color=delta_color)
        m3.metric("Lifetime Score", f"{final_lifetime_score}", "XP")
        m4.metric("Daily Consistency", f"{d_score}%", "Excl. Connect")

        st.divider()
        st.subheader("📈 Trends & Consistency")
        tab1, tab2, tab3 = st.tabs(["📊 Charts", "🔥 Heatmap", "🏆 Jackpot & Review"])
        
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
            is_sunday = today.weekday() == 6
            retro_title = "📝 Weekly Review (Unlock on Sunday)"
            if is_sunday: retro_title = "📝 Weekly Review (Open Now!)"
            st.markdown(f"#### {retro_title}")
            
            if is_sunday:
                st.markdown(f"**Reviewing Week {curr_week}** (Progress: {cur_pct}%)")
                st.warning(f"⚠️ **Focus Area:** You missed **{missed_msg}** most this week.")
                
                with st.form("weekly_retro_form"):
                    q1 = st.text_input("1. 🏆 Big Win:", placeholder="e.g. Hit all workouts")
                    q2 = st.text_input("2. 📉 Big Miss:", placeholder="e.g. Procrastinated coding")
                    q3 = st.text_input("3. 🧐 Why it happened?", placeholder="e.g. Stayed up too late")
                    q4 = st.text_input("4. 🛠️ The Fix:", placeholder="e.g. Phone off at 10pm")
                    q5 = st.slider("5. 🔥 Commitment for Next Week?", 1, 10, 8)
                    if st.form_submit_button("Save Weekly Review"):
                        full_review = f"{q1}|{q2}|{q3}|{q4}|{q5}"
                        save_generic_text(today, "Weekly_Retro", full_review)
            else:
                st.info("🔒 This form is locked until Sunday. Focus on your daily tasks for now!")
            
            st.divider()
            st.markdown("### 📜 Past Reviews & Ledger")
            st.metric("Total Career Earnings", f"{total_historical_jackpot} Pts")
            
            if history_log:
                history_log.sort(key=lambda x: x['Week'], reverse=True)
                for entry in history_log:
                    with st.container():
                        c_head, c_pts = st.columns([3, 1])
                        c_head.markdown(f"#### **{entry['Week']}** - {entry['Status']}")
                        c_pts.metric("Pts", entry['Points'])
                        
                        raw_retro = entry['Retrospective']
                        if raw_retro and "|" in raw_retro:
                            parts = raw_retro.split("|")
                            if len(parts) >= 4:
                                st.markdown(f"- 🏆 **Win:** {parts[0]}\n- 📉 **Miss:** {parts[1]}\n- 🧐 **Why:** {parts[2]}\n- 🛠️ **Fix:** {parts[3]}\n- 🔥 **Commitment:** {parts[4]}/10")
                            else: st.text(f"📝 Note: {raw_retro}")
                        elif raw_retro: st.text(f"📝 Note: {raw_retro}")
                        else: st.caption("No review submitted.")
                        st.divider()
            else:
                st.info("No history yet.")

        with st.popover("🔐 View Raw Data (PIN Required)"):
            pin = st.text_input("Enter PIN:", type="password", key="history_pin")
            if pin == "1234":
                st.dataframe(df.sort_values("Date", ascending=False))
            elif pin:
                st.error("🔒 Incorrect PIN")
