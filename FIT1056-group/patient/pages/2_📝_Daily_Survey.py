import streamlit as st
from datetime import datetime
from components.ui import apply_theme, page_header, card, require_auth
from app.patient import PatientService

st.set_page_config(page_title="Daily Survey", page_icon="📝", layout="centered")
apply_theme()
require_auth()
page_header("Daily Survey", "Log your well-being", "📝")

svc = PatientService()
pid = st.session_state["auth_user"]

with card("New entry"):
    mood = st.selectbox("Mood", ["Great","Good","Okay","Low","Bad"])
    pain = st.slider("Pain level (0-10)", 0, 10, 3)
    sleep = st.slider("Sleep quality (0-10)", 0, 10, 6)
    meds = st.checkbox("Took medication")
    note = st.text_area("Notes (optional)")
    if st.button("Submit"):
        svc.add_survey(pid, {"mood": mood, "pain": pain, "sleep": sleep, "meds": bool(meds), "note": note})
        st.success("Survey saved.")

with card("History (latest 30)"):
    items = list(reversed(svc.get_surveys(pid)))[:30]
    if not items:
        st.info("No entries yet.")
    else:
        for s in items:
            st.write(f"• **{s.get('ts','')}** — Mood: {s.get('mood')} | Pain: {s.get('pain')} | Sleep: {s.get('sleep')} | Meds: {s.get('meds')} ")
            if s.get("note"):
                st.caption(s["note"])
