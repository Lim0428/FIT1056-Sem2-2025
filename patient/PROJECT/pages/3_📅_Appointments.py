import streamlit as st
from datetime import datetime, date, time
from components.ui import require_auth, apply_theme, page_header, card
from services.appointments import AppointmentService

st.set_page_config(page_title="Appointments", page_icon="📅", layout="centered")
apply_theme()
require_auth()

pid = st.session_state.auth_user
svc = AppointmentService()

page_header("Appointments", "Book and review your visits", "📅")

with card("Book new appointment"):
    with st.form("appt_form"):
        appt_date = st.date_input("Date", value=date.today())
        appt_time = st.time_input("Time", value=time(10, 0))
        note = st.text_area("Reason / notes")
        submitted = st.form_submit_button("Book appointment")

if submitted:
    ok, msg = svc.book(pid, datetime.combine(appt_date, appt_time), note.strip())
    if ok:
        st.success("Appointment booked.")
    else:
        st.error(msg)

with card("My Appointments"):
    items = svc.list_by_patient(pid)
    if not items:
        st.info("No appointments.")
    else:
        for a in items:
            st.write(f"- {a['dt']} — {a.get('note','(no note)')}")
    st.caption("Basic conflict prevention is enforced (no double-booking for the same time).")
