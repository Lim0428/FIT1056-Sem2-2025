import streamlit as st
from datetime import datetime
from components.ui import require_auth, apply_theme, page_header, card
from services.patient import PatientService

st.set_page_config(page_title="Feedback", page_icon="🗳️", layout="centered")
apply_theme()
require_auth()

pid = st.session_state.auth_user
svc = PatientService()

page_header("Feedback", "Tell us how we're doing", "🗳️")

with card("Write feedback"):
    with st.form("feedback_form"):
        rating = st.slider("Overall experience", 1, 5, 4)
        text = st.text_area("Your feedback")
        submitted = st.form_submit_button("Submit feedback")

if submitted:
    svc.add_feedback(pid, {"ts": datetime.utcnow().isoformat(), "rating": int(rating), "text": text.strip()})
    st.success("Feedback submitted. Thank you!")

with card("My Feedback"):
    fb = svc.get_feedback(pid)
    if not fb:
        st.info("No feedback yet.")
    else:
        for f in reversed(fb[-20:]):
            st.write(f"- {f['ts']} — ⭐ {f['rating']}/5")
            if f["text"]:
                st.caption(f["text"])
