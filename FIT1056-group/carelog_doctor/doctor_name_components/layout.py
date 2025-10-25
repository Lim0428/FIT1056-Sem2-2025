# doctor_name_components/layout.py
import streamlit as st

def topbar():
    st.markdown(
        """
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:22px; font-weight:700;">CareLog • Doctor Portal</span>
            <span class="pill">v2.0</span>
          </div>
          <div class="muted" style="font-size:14px;">
            Secure • RBAC • Consent-gated
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

def sidebar_menu():
    with st.sidebar:
        st.markdown("### Navigation")
        choice = st.radio(
            "Go to",
            ["Dashboard", "My Profile", "Patients", "Encounters", "Appointments", "Appointment History", "Messages"],
            label_visibility="collapsed",
            key="sidebar_nav_radio",
            index=["Dashboard", "My Profile", "Patients", "Encounters", "Appointments", "Appointment History", "Messages"].index(
                st.session_state.get("nav", "Dashboard")
            ),
        )
        return choice
