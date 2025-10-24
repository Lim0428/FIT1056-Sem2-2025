# doctor_name_pages/appointments.py
import streamlit as st
from datetime import datetime

def _get_appt_by_id(store, appt_id):
    # Try a direct method first
    if hasattr(store, "get_appointment"):
        appt = store.get_appointment(appt_id)
        if appt: return appt

    # Fallback: search common lists
    if hasattr(store, "list_all_appointments"):
        for a in store.list_all_appointments() or []:
            if a.get("id") == appt_id:
                return a
    if hasattr(store, "list_upcoming_appointments"):
        for a in store.list_upcoming_appointments(limit=5000) or []:
            if a.get("id") == appt_id:
                return a
    return None

def page_appointments(store):
    st.markdown("### Appointment")

    appt_id = st.session_state.get("selected_appt_id")
    if not appt_id:
        st.info("No appointment selected from the dashboard.")
        if st.button("Back to Dashboard"):
            st.session_state["nav"] = "dashboard"
            st.rerun()
        return

    appt = _get_appt_by_id(store, appt_id)
    if not appt:
        st.error("Appointment not found.")
        if st.button("Back to Dashboard"):
            st.session_state["nav"] = "dashboard"
            st.rerun()
        return

    # Pretty time formatting
    def fmt(iso):
        try:
            return datetime.fromisoformat(iso.replace("Z","")).strftime("%d %b %Y • %I:%M %p")
        except Exception:
            return iso

    st.markdown(
        f"""
        <div style="background: rgba(255,255,255,0.06);
                    border:1px solid rgba(255,255,255,0.10);
                    border-radius:16px; padding:16px;">
          <div style="font-weight:700; font-size:18px; margin-bottom:6px;">
            {appt.get('patient_name') or f"Patient #{appt.get('patient_id','—')}"}
          </div>
          <div style="color:#9AA4B2; margin-bottom:10px;">
            Reason: {appt.get('reason','—')}
          </div>
          <div><b>Start:</b> {fmt(appt.get('start',''))}</div>
          <div><b>End:</b> {fmt(appt.get('end',''))}</div>
          <div><b>Status:</b> {appt.get('status','—')}</div>
          <div><b>Location:</b> {appt.get('location','—')}</div>
          <div style="margin-top:10px;"><b>Notes:</b><br/>{appt.get('notes','—')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")
    cols = st.columns(2)
    with cols[0]:
        if st.button("Back to Dashboard", use_container_width=True, type="secondary"):
            st.session_state["nav"] = "dashboard"
            st.rerun()
    with cols[1]:
        st.button("Edit (coming soon)", use_container_width=True, type="secondary")
