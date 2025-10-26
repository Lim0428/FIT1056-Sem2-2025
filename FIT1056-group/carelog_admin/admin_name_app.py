# admin_name_app.py
import streamlit as st

from admin_name_utils.theme import inject_theme
from admin_name_utils.storage import bootstrap_store
from admin_name_utils.auth import ensure_auth, login_panel, logout_button

from admin_name_ui import (
    dashboard as ui_dashboard,
    user_management as ui_user_mgmt,
    doctor_management as ui_doctor_mgmt,
    patient_management as ui_patient_mgmt,
    scheduling as ui_scheduling,
    room_allocation as ui_rooms,
    billing as ui_billing,
    reports as ui_reports,
    alerts as ui_alerts,
)

PAGES = {
    "🏠 Dashboard": ui_dashboard.render,
    "👥 User Management": ui_user_mgmt.render,
    "🩺 Doctor Management": ui_doctor_mgmt.render,
    "👤 Patient Management": ui_patient_mgmt.render,
    "📅 Scheduling": ui_scheduling.render,
    "🛏️ Rooms & Resources": ui_rooms.render,
    "💳 Billing": ui_billing.render,
    "📊 Reports": ui_reports.render,
    "🚨 Alerts": ui_alerts.render,
}

def main():
    # must be first Streamlit call
    st.set_page_config(page_title="CareLog Admin", page_icon="🛡️", layout="wide")

    inject_theme()
    bootstrap_store()

    # -------- Not logged in: show login form in the main area --------
    if not ensure_auth("admin"):
        login_panel()
        return

    # -------- Logged in: show sidebar and page --------
    with st.sidebar:
        st.markdown("## 🛡️ CareLog Admin")
        page_key = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
        st.divider()
        logout_button()

    PAGES[page_key]()

if __name__ == "__main__":
    main()
