# medical_staff/pages/3_📝_Observations.py
import streamlit as st
from components.ui import apply_theme, page_header, card
from components.staff_shared import pick_staff_and_patient
from app.medical_staff import MedicalStaffService

st.set_page_config(page_title="Observations", page_icon="📝", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Observations", "Record and review observations.", "📝")

staff_id, patient = pick_staff_and_patient("obs_pick")
if not patient:
    st.stop()
pid = patient["id"]

with card("Record observation"):
    c1, c2, c3, c4 = st.columns(4)
    with c1: mood = st.select_slider("Mood", ["Very Sad","Sad","Neutral","Happy","Very Happy"], value="Neutral", key=f"obs_mood_{pid}")
    with c2: pain = st.slider("Pain (0–10)", 0, 10, 0, key=f"obs_pain_{pid}")
    with c3: sleep = st.selectbox("Sleep", ["Poor","Average","Good"], index=1, key=f"obs_sleep_{pid}")
    with c4: appetite = st.selectbox("Appetite", ["Poor","Moderate","Good"], index=1, key=f"obs_appetite_{pid}")
    notes = st.text_area("Notes", key=f"obs_notes_{pid}")
    if st.button("📝 Save observation", type="primary", key=f"obs_save_{pid}"):
        o = svc.record_observation(staff_id, pid, mood, pain, sleep, appetite, notes)
        st.success(f"Saved at {o.timestamp}")

with card("Recent observations (30 days)"):
    obs_items = svc.list_observations(pid, days=30, limit=200)
    if not obs_items: st.caption("No observations yet.")
    else:
        for o in obs_items:
            st.write(f"• **{o['timestamp']}** — Mood **{o['mood']}**, Pain **{o['pain']}**, "
                     f"Sleep **{o['sleep']}**, Appetite **{o['appetite']}** — _{o['notes'] or '(no notes)'}_")
