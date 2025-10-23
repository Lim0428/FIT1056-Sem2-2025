import streamlit as st
from datetime import datetime, timedelta
from doctor_name_services.appointments import (
    list_my_appointments, create_or_move_appointment, cancel_appointment
)
from doctor_name_components.tables import table_appointments

def page_appointments(store):
    st.subheader("Appointments & Schedule (Conflict Prevention)")
    appts = list_my_appointments(store)
    table_appointments(appts)

    st.markdown("#### Create / Reschedule")
    with st.form("appt_form"):
        pid = st.text_input("Patient ID")
        start_dt = st.text_input("Start (YYYY-MM-DD HH:MM)")
        end_dt = st.text_input("End (YYYY-MM-DD HH:MM)")
        reason = st.text_input("Reason")
        submitted = st.form_submit_button("Save", use_container_width=True)
        if st.button("Cancel Appointment", use_container_width=True):


            try:
                start = datetime.fromisoformat(start_dt.replace(" ", "T"))
                end = datetime.fromisoformat(end_dt.replace(" ", "T"))
                ok, msg = create_or_move_appointment(store, pid.strip(), start, end, reason)
                if ok:
                    st.success("Saved.")
                    st.rerun()
                else:
                    st.error(msg)
            except Exception as e:
                st.error(f"Invalid datetime: {e}")

    st.markdown("#### Cancel")
    appt_id = st.text_input("Appointment ID to cancel")
    if st.button("Cancel Appointment"):
        ok, msg = cancel_appointment(store, appt_id.strip())
        if ok:
            st.success("Cancelled and slot reopened.")
            st.rerun()
        else:
            st.error(msg)
