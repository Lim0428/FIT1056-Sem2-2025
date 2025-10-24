import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

from components.ui import (
    apply_desktop_css,
    page_header,
    stat,
    action_card,
    card,
)
from services.data_store import (
    list_assigned_patients,
    list_tasks,
    list_notifications,
)

st.set_page_config(page_title="Nurse • Overview", page_icon="🩺", layout="wide")
apply_desktop_css()  # default 1400px width

nurse_id = st.session_state.get("nurse_id", "nurse_1")

# Header
today = datetime.now().strftime("%a, %d %b %Y")
page_header("Nurse Overview", subtitle=f"Welcome back • {today}", right="v2.0")

# KPI row
c1, c2, c3, c4 = st.columns(4)
with c1: stat("Assigned Patients", str(len(list_assigned_patients(nurse_id))))
with c2: stat("Tasks Due Today", str(sum(1 for t in list_tasks(nurse_id) if not t.get("completed"))))
with c3: stat("Unread Alerts", str(sum(1 for n in list_notifications(nurse_id) if not n.get("ack"))))
with c4: stat("Recent Entries (7d)", "1")

st.divider()

# Quick actions (tiles are the only click targets)
st.subheader("Quick actions")

qa1, qa2 = st.columns(2, gap="large")
with qa1:
    action_card("Administer medications", "Open MAR to record drug • dose • route", "💊",
            target_page="pages/3_💊_Medication_MAR.py", key="qa_mar")

with qa2:
    action_card(
        "Record vitals",
        "Temperature • BP • HR • auto-timestamped",
        "📈",
        target_page="pages/4_📈_Vitals_Notes.py",
        key="qa_vitals",
    )

qa3, qa4 = st.columns(2, gap="large")
with qa3:
    action_card(
        "Add care note",
        "Document observations/assessments to timeline",
        "🧑‍⚕️",
        target_page="pages/4_📈_Vitals_Notes.py",
        key="qa_note",
    )
with qa4:
    action_card(
        "View my tasks",
        "Prioritized list • mark complete • high-risk flag",
        "🗓️",
        target_page="pages/5_🗓️_Tasks.py",
        key="qa_tasks",
    )

st.divider()

# Alerts + Today's work
left, right = st.columns([1.1, 1.2], gap="large")

with left:
    st.subheader("Urgent alerts")
    alerts = [n for n in list_notifications(nurse_id) if not n.get("ack")]
    if not alerts:
        card("All clear", "No new alerts 🎉")
    else:
        for n in alerts:
            body = f"**{n['title']}**  \n{n['ts']}  \n{n['body']}"
            card("New alert", body)

with right:
    st.subheader("Today’s work")
    # Mini trend chart
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    hours = pd.date_range(now.replace(hour=0), periods=24, freq="h")
    df = pd.DataFrame({
        "time": hours,
        "minutes": [max(6, int(abs(40 + 20*__import__('math').sin(i/3)))) for i in range(24)],
    })
    chart = alt.Chart(df).mark_area(interpolate="monotone", opacity=0.7).encode(
        x=alt.X("time:T", title="Time"),
        y=alt.Y("minutes:Q", title="Duty Minutes"),
    ).properties(height=240)
    st.altair_chart(chart, use_container_width=True)

    # Task preview
    tasks = list_tasks(nurse_id)
    if tasks:
        lines = []
        for t in tasks[:6]:
            state = "✅" if t.get("completed") else "⬜"
            lines.append(f"{state} **{t['title']}** • due **{t['due']}** • patient **{t['patient_id']}**")
        card("Tasks (preview)", "<br>".join(lines))
    else:
        card("Tasks (preview)", "No tasks assigned.")

st.caption("Secure • RBAC • Audit-logged")
