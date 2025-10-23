import streamlit as st
# --- SAFE IMPORT PATH PATCH (place at the very top of app.py) ---
import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
# ----------------------------------------------------------------

from doctor_name_app.theme import inject_theme
from doctor_name_services.auth import ensure_bootstrap_files, login_form, logout, is_authenticated
from doctor_name_components.layout import topbar, sidebar_menu
from doctor_name_services.data_store import DataStore
from doctor_name_pages.dashboard import page_dashboard
from doctor_name_pages.profile import page_profile
from doctor_name_pages.patient import page_patients
from doctor_name_pages.encounters import page_encounters
from doctor_name_pages.appointments import page_appointments
from doctor_name_pages.messages import page_messages
from doctor_name_pages.dashboard import page_dashboard

st.set_page_config(page_title="CareLog • Doctor Portal", page_icon="🩺", layout="wide")
inject_theme()
ensure_bootstrap_files()

if "nav" not in st.session_state:
    st.session_state.nav = "Dashboard"

if not is_authenticated():
    login_form()
    st.stop()

# Layout
topbar()
nav = sidebar_menu()

# Data store (singleton-style for this session)
store = DataStore()

# Router
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
elif nav == "Messages":
    page_messages(store)
else:
    st.error("Unknown page")

st.sidebar.divider()
if st.sidebar.button("Logout", use_container_width=True):
    

    logout()
    st.rerun()
