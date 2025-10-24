# app.py
from __future__ import annotations
import sys
from pathlib import Path
import streamlit as st

# --- Path bootstrap (so relative imports work when running `streamlit run app.py`) ---
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# --- Theme / Layout / Services / Pages ---
from doctor_name_app.theme import inject_theme
from doctor_name_components.layout import topbar, sidebar_menu
from doctor_name_services.auth import ensure_bootstrap_files, login_form, logout, is_authenticated
from doctor_name_services.data_store import DataStore

from doctor_name_pages.dashboard import page_dashboard
from doctor_name_pages.profile import page_profile
from doctor_name_pages.patient import page_patients
from doctor_name_pages.encounters import page_encounters
from doctor_name_pages.appointments import page_appointments
from doctor_name_pages.appointments_history import page_appointments_history
from doctor_name_pages.messages import page_messages

# --- App config & theme ---
st.set_page_config(page_title="CareLog • Doctor Portal", page_icon="🩺", layout="wide")
inject_theme()
ensure_bootstrap_files()

# --- Auth gate ---
if not is_authenticated():
    login_form()
    st.stop()

# --- Session defaults ---
if "nav" not in st.session_state:
    st.session_state["nav"] = "Dashboard"

# Normalize any lowercase / programmatic values
st.session_state["nav"] = {
    "dashboard": "Dashboard",
    "appointments": "Appointments",
    "appointment history": "Appointment History",
    "messages": "Messages",
    "patients": "Patients",
    "my profile": "My Profile",
    "encounters": "Encounters",
}.get(str(st.session_state["nav"]).lower(), st.session_state["nav"])

# --- Top bar ---
topbar()

# If a page pushed a route (e.g., from a "View" button), honor it for this run
route_push = st.session_state.pop("_route_push", False)

# --- Sidebar (rendered exactly once) ---
if not route_push:
    # Let user change the page from the sidebar radio
    nav_choice = sidebar_menu()  # this radio has a fixed key inside layout.py
    if nav_choice != st.session_state["nav"]:
        st.session_state["nav"] = nav_choice
else:
    # If a push was requested, still render the sidebar for layout consistency
    _ = sidebar_menu()  # ignore its value this run

# Optional: Logout control at the bottom of the sidebar
st.sidebar.divider()
if st.sidebar.button("Logout", use_container_width=True, key="logout_btn"):
    logout()
    st.rerun()

# --- Data store (per-session) ---
store = DataStore()

# --- Router (use session state's single source of truth) ---
nav = st.session_state["nav"]

if nav == "Dashboard":
    page_dashboard(store)
elif nav == "My Profile":
    page_profile(store)
elif nav == "Patients":
    page_patients(store)
elif nav == "Encounters":
    page_encounters(store)
elif nav == "Appointments":
    page_appointments(store)
elif nav == "Appointment History":
    page_appointments_history(store)
elif nav == "Messages":
    page_messages(store)
else:
    st.error(f"Unknown page: {nav}")
