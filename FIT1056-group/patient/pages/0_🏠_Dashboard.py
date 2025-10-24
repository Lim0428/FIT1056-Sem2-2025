# pages/0_🏠_Dashboard.py
import streamlit as st
from datetime import datetime, date
from statistics import mean
from typing import List, Dict, Any

from components.ui import apply_theme, page_header, card, require_auth
from app.patient import PatientService
from app.appointments import AppointmentService
from app.messaging import MessagingService
from app.auth import AuthService

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")
apply_theme()
require_auth()
page_header("Your Dashboard", "Snapshot of your health & activity", "🏠")

pid = st.session_state["auth_user"]
patient_svc = PatientService()
appt_svc = AppointmentService()
msg_svc = MessagingService()
auth_svc = AuthService()

# ---------- helpers ----------
def parse_iso(dt_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None

def star_str(n: int) -> str:
    n = max(0, min(5, int(n or 0)))
    return "★" * n + "☆" * (5 - n)

def next_appointment(appts: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    future = []
    now = datetime.now()
    for a in appts:
        ts = parse_iso(a.get("dt", ""))
        if ts and ts >= now:
            future.append((ts, a))
    future.sort(key=lambda x: x[0])
    return future[0][1] if future else None

# ---------- fetch data ----------
profile = patient_svc.get(pid) or {}
surveys = patient_svc.get_surveys(pid) or []
feedbacks = patient_svc.get_feedback(pid) or []
messages = msg_svc.list_by_patient(pid) or []
appointments = appt_svc.list_by_patient(pid) or []
login_events = auth_svc.get_login_history(pid) or []

latest_survey = surveys[-1] if surveys else {}
avg_pain = round(mean([s.get("pain", 0) for s in surveys[-10:]]), 1) if surveys else 0.0
avg_sleep = round(mean([s.get("sleep", 0) for s in surveys[-10:]]), 1) if surveys else 0.0
latest_mood = (latest_survey.get("mood") or "—")
upcoming = next_appointment(appointments)
avg_rating = round(mean([int(f.get("rating", 0)) for f in feedbacks]), 1) if feedbacks else 0.0
last_login = (login_events[-1]["ts"] if login_events else "—")

# ---------- top KPIs ----------
col1, col2, col3, col4 = st.columns(4)
with col1:
    with card("Next appointment"):
        if upcoming:
            when = parse_iso(upcoming["dt"])
            st.metric("Date", when.strftime("%a, %d %b %Y"))
            st.caption(f"Time: {when.strftime('%I:%M %p')}  •  Note: {upcoming.get('note','(none)')}")
        else:
            st.write("No upcoming appointment")

with col2:
    with card("Mood • Pain • Sleep"):
        st.metric("Latest mood", latest_mood)
        st.caption(f"Avg pain (last 10): **{avg_pain} / 10**")
        st.caption(f"Avg sleep (last 10): **{avg_sleep} / 10**")

with col3:
    with card("Messages"):
        st.metric("Total sent", len(messages))
        last = messages[-1] if messages else None
        st.caption(f"Last: {last.get('to_role')} • {last.get('ts')}" if last else "No messages yet")

with col4:
    with card("Feedback"):
        st.metric("Average rating", f"{avg_rating}/5")
        st.caption(star_str(round(avg_rating)))

# ---------- profile mini card ----------
with card("Profile"):
    n_cols = st.columns(3)
    with n_cols[0]:
        st.write(f"**Name**: {profile.get('name', '—')}")
        st.write(f"**DOB**: {profile.get('dob','—')}")
        st.write(f"**Gender**: {profile.get('gender','—')}")
    with n_cols[1]:
        st.write(f"**Language**: {profile.get('pref_language','—')}")
        st.write(f"**Food**: {profile.get('pref_food','—')}")
        st.write(f"**Preferred nurse**: {profile.get('pref_nurse_gender','—')}")
    with n_cols[2]:
        vis = profile.get("visible_to_non_primary", False)
        st.write(f"**Visibility**: {'Allowed' if vis else 'Restricted'}")
        st.write(f"**Emergency**: {profile.get('emergency_contact','—')}")

# ---------- activity stream ----------
left, right = st.columns([1.15, 1])
with left:
    with card("Recent surveys"):
        if not surveys:
            st.info("No surveys yet. Try logging one on the Daily Survey page.")
        else:
            for s in list(reversed(surveys[-6:])):
                ts = s.get("ts", "")
                st.write(
                    f"**{ts}** — Mood: {s.get('mood','?')} | "
                    f"Pain: {s.get('pain','?')} | Sleep: {s.get('sleep','?')} | "
                    f"Meds: {'✓' if s.get('meds') else '—'}"
                )
with right:
    with card("Recent messages"):
        if not messages:
            st.info("No messages yet.")
        else:
            for m in list(reversed(messages[-6:])):
                st.write(f"**{m['ts']}** → {m['to_role']}: {m['content']}")

    with card("Recent feedback"):
        if not feedbacks:
            st.info("No feedback yet.")
        else:
            for f in list(reversed(feedbacks[-4:])):
                stars = star_str(int(f.get("rating", 0)))
                st.write(f"**{f['ts']}** — {stars}")
                if f.get("text"):
                    st.caption(f["text"])

# ---------- quick actions ----------
with card("Quick actions"):
    qa = st.columns([1,1,1,1,1,1])
    qa[0].page_link("pages/1_👤_Profile_&_Preferences.py", label="Edit profile", icon="👤")
    qa[1].page_link("pages/2_📝_Daily_Survey.py", label="New survey", icon="📝")
    qa[2].page_link("pages/3_📅_Appointments.py", label="Book appointment", icon="📅")
    qa[3].page_link("pages/4_💬_Messages.py", label="Send message", icon="💬")
    qa[4].page_link("pages/5_🗳️_Feedback.py", label="Give feedback", icon="🗳️")
    qa[5].page_link("pages/6_🔐_Login_History.py", label="Login history", icon="🔐")
