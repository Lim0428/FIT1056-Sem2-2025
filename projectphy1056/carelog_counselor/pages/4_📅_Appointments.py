# counselor_name_pages/4_📅_Appointments.py
import streamlit as st
from datetime import datetime, timedelta, time as dtime
from counselor_name_components.ui import apply_theme, top_nav, require_auth
from counselor_name_app.services.appointments import AppointmentService
from counselor_name_app.services.patients import PatientService

st.set_page_config(page_title="Appointments", page_icon="📅", layout="wide")
apply_theme(); require_auth(); top_nav("Appointments")

svc = AppointmentService()
ps = PatientService()
me = st.session_state["auth_user"]

def compose_dt(d, t) -> datetime:
    return datetime.combine(d, t)

st.subheader("Book a session")

pids = [p["id"] for p in ps.list_assigned(me)]
if not pids:
    st.info("No assigned patients.")
    st.stop()

col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
with col1:
    pid = st.selectbox("Patient", pids)

# Defaults: next whole hour for start, +1 hour for end
now = datetime.now()
default_start_dt = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
default_end_dt   = default_start_dt + timedelta(hours=1)

with col2:
    start_date = st.date_input("Start date", value=default_start_dt.date())
    start_time = st.time_input("Start time", value=default_start_dt.time())
with col3:
    end_date = st.date_input("End date", value=default_end_dt.date())
    end_time = st.time_input("End time", value=default_end_dt.time())
with col4:
    kind = st.selectbox("Type", ["Individual", "Group", "Follow-up"])

start_dt = compose_dt(start_date, start_time)
end_dt = compose_dt(end_date, end_time)

if end_dt <= start_dt:
    st.error("End must be after start.")
else:
    if st.button("Book", type="primary"):
        try:
            ap = svc.book(pid, me, start_dt.isoformat(), end_dt.isoformat(), kind)
            st.success(f"Booked {ap['id']} · {start_dt:%Y-%m-%d %H:%M} — {end_dt:%H:%M}")
            st.rerun()
        except Exception as e:
            st.error(str(e))

st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

st.subheader("Your upcoming sessions")
appts = svc.list_for_counselor(me)
if not appts:
    st.info("No upcoming sessions yet.")
else:
    # sort by start time ascending
    appts = sorted(appts, key=lambda a: datetime.fromisoformat(a["start"]))
    for ap in appts:
        s = datetime.fromisoformat(ap["start"]); e = datetime.fromisoformat(ap["end"])
        st.write(f"• {s:%Y-%m-%d %H:%M} – {e:%H:%M} with **{ap['patient_id']}** ({ap['kind']}) — {ap['status']}")
