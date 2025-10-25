# app.py
from __future__ import annotations
import sys
from pathlib import Path
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# THEME
from doctor_name_app.theme import inject_theme, force_text_white

# NAV + DATA
from doctor_name_components.layout import topbar, sidebar_menu
from doctor_name_services.data_store import DataStore

# PAGES
from doctor_name_pages.dashboard import page_dashboard
from doctor_name_pages.profile import page_profile
from doctor_name_pages.patient import page_patients
from doctor_name_pages.encounters import page_encounters
from doctor_name_pages.appointments import page_appointments
from doctor_name_pages.appointments_history import page_appointments_history
from doctor_name_pages.messages import page_messages

# ----- App settings -----
st.set_page_config(page_title="CareLog • Doctor Portal", page_icon="🩺", layout="wide")
inject_theme()
force_text_white()

# ----- BYPASS LOGIN (dev mode) -----
# We set a default doctor in session so pages relying on `current_doctor()` work.
if "auth" not in st.session_state:
    # Minimal identity (should match an id in your /data/doctors.json)
    st.session_state["auth"] = {
        "doctor": {
            "id": "doc1",
            "email": "dr.lim@carelog.com",
            "name": "Dr. Lim Wei Han",
        }
    }

# ----- Navigation state -----
if "nav" not in st.session_state:
    st.session_state["nav"] = "Dashboard"

# If a page pushed a route (e.g., from dashboard "See more")
route_push = st.session_state.pop("_route_push", False)

# ----- Layout: topbar + (maybe) sidebar -----
topbar()

# Only read the sidebar menu if a route wasn't programmatically pushed this run.
if not route_push:
    choice = sidebar_menu()
    if choice:
        st.session_state["nav"] = choice

nav = st.session_state["nav"]
store = DataStore()  # uses shared /data folder per your latest data_store.py

# ----- Routing -----
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
    st.error("Unknown page")

# NOTE: No Logout button anymore (auth is bypassed).
