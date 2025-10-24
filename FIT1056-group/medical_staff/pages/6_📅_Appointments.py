# medical_staff/pages/6_📅_Appointments.py
from datetime import datetime, timedelta
import streamlit as st
from components.ui import apply_theme, page_header, card
from components.staff_shared import pick_staff_and_patient
from app.medical_staff import MedicalStaffService

st.set_page_config(page_title="Appointments", page_icon="📅", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Appointments", "View / reschedule / cancel", "📅")

staff_id, patient = pick_staff_and_patient("appt_pick")
if not patient:
    st.stop()
pid = patient["id"]

with card("Upcoming (90 days)"):
    now = datetime.now(); in_90 = (now + timedelta(days=90)).isoformat(timespec="minutes")
    appts = svc.list_appointments(for_patient=pid, to_iso=in_90)
    if not appts: st.caption("No upcoming appointments.")
    else:
        for a in appts:
            when = a.get("dt",""); appt_id = a.get("id"); status = a.get("status","scheduled")
            st.write(f"• **{when}** — status: **{status}** — (ID: `{appt_id}`)")
            c1, c2, _ = st.columns([2,2,6])
            with c1:
                new_dt = st.text_input("Reschedule to (ISO)", value=when, key=f"appt_resiso_{appt_id}")
                if st.button("Reschedule", key=f"appt_resbtn_{appt_id}"):
                    ok, msg = svc.reschedule_appointment(appt_id, new_dt, staff_id); st.success(msg) if ok else st.error(msg)
            with c2:
                if st.button("Cancel", key=f"appt_cancel_{appt_id}"):
                    ok, msg = svc.cancel_appointment(appt_id, staff_id); st.success(msg) if ok else st.error(msg)
