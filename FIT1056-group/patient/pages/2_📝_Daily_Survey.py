# pages/2_📝_Daily_Survey.py
import streamlit as st
from components.ui import apply_theme, page_header, card, require_auth, divider
from app.patient import PatientService

st.set_page_config(page_title="Daily Survey", page_icon="📝", layout="wide")
apply_theme()
require_auth()
page_header("Daily Survey", "Log how you’re feeling today", "📝")

svc = PatientService()
pid = st.session_state["auth_user"]

# ---------------- Composer ----------------
with card("New entry"):
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        mood = st.selectbox("Mood", ["", "Great", "Good", "Okay", "Bad", "Awful"], index=0)
    with c2:
        pain = st.slider("Pain (0 none → 10 worst)", 0, 10, 0)
    with c3:
        sleep = st.number_input("Sleep (hours)", min_value=0.0, max_value=24.0, step=0.5, value=0.0)

    col_meds, col_note = st.columns([1,3])
    with col_meds:
        meds = st.toggle("Took meds today", value=False)
    with col_note:
        note = st.text_area("Notes (optional)", placeholder="Anything else you'd like to add?")

    if st.button("➕ Save entry", type="primary"):
        ok = svc.add_survey(pid, {"mood": mood, "pain": pain, "sleep": sleep, "meds": meds, "note": note})
        if ok:
            st.success("Saved ✓")
            st.rerun()
        else:
            st.error("Could not save your entry.")

divider()

# ---------------- History ----------------
with card("History"):
    items = svc.get_surveys(pid)
    if not items:
        st.caption("No survey entries yet.")
    else:
        # Display compact list
        for i, s in enumerate(items, start=1):
            st.markdown(
                f"**{i}. {s.get('ts','—')}**  \n"
                f"- Mood: **{s.get('mood','—')}**  \n"
                f"- Pain: **{s.get('pain','—')}**  \n"
                f"- Sleep: **{s.get('sleep','—')}h**  \n"
                f"- Took meds: **{'Yes' if s.get('meds') else 'No'}**  \n"
                f"- Note: {s.get('note','—') or '—'}"
            )
            st.divider()
