import streamlit as st
from datetime import datetime
from components.ui import require_auth, apply_theme, page_header, card, badge, divider
from services.patient import PatientService

st.set_page_config(page_title="Daily Survey", page_icon="📝", layout="centered")
apply_theme()
require_auth()

pid = st.session_state.auth_user
svc = PatientService()

page_header("Daily Well-being Survey", "Mood, pain, sleep quality, and medication status", "📝")
badge("Your last 30 entries are shown below.")

with card("New entry"):
    with st.form("survey_form"):
        mood = st.slider("Mood (0=low, 10=great)", 0, 10, 5)
        pain = st.slider("Pain level (0=none, 10=worst)", 0, 10, 2)
        sleep = st.selectbox("Sleep quality", ["Poor", "Fair", "Good", "Excellent"], index=2)
        took_meds = st.radio("Medication taken?", ["Yes", "No"], index=0, horizontal=True)
        note = st.text_area("Optional note")
        submitted = st.form_submit_button("Submit survey")

if submitted:
    svc.add_survey(pid, {
        "ts": datetime.utcnow().isoformat(),
        "mood": int(mood),
        "pain": int(pain),
        "sleep": sleep,
        "meds": (took_meds == "Yes"),
        "note": note.strip()
    })
    st.success("Survey recorded.")

divider()
page_header("History", "", "📜")
history = svc.get_surveys(pid)
if not history:
    st.info("No surveys yet.")
else:
    for s in reversed(history[-30:]):
        with card():
            st.write(f"**{s['ts']}** — Mood {s['mood']}, Pain {s['pain']}, Sleep {s['sleep']}, Meds: {'Yes' if s['meds'] else 'No'}")
            if s.get("note"):
                st.caption(s["note"])
