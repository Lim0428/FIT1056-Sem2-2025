# medical_staff/main.py
import streamlit as st
from components.ui import apply_theme, card, page_header

st.set_page_config(page_title="CareLog • Staff", page_icon="🩺", layout="centered")
apply_theme()

# Sidebar nav (each is a real page under /pages)
with st.sidebar:
    st.title("Medical Staff")
    st.page_link("pages/0_🏠_Dashboard.py",     label="🏠 Dashboard")
    st.page_link("pages/1_🌡️_Vitals.py",       label="🌡️ Vitals")
    st.page_link("pages/2_💊_MAR.py",          label="💊 Medication (MAR)")
    st.page_link("pages/3_📝_Observations.py",  label="📝 Observations")
    st.page_link("pages/4_✅_Tasks.py",         label="✅ Tasks")
    st.page_link("pages/5_🔄_Handover.py",      label="🔄 Handover")
    st.page_link("pages/6_📅_Appointments.py",  label="📅 Appointments")
    st.page_link("pages/7_💬_Messages.py",      label="💬 Messages")
    st.page_link("pages/8_📄_Documents.py",     label="📄 Documents")
    st.page_link("pages/9_🧾_Audit.py",         label="🧾 Audit")

page_header("CareLog • Medical Staff", "Choose a tool from the sidebar.", "🩺")

with card("Quick tips"):
    st.write(
        "- Use **Dashboard** to confirm the app is running.\n"
        "- Each page has a **patient & staff picker** at the top.\n"
        "- Data is saved to the JSON files under `data/`."
    )
