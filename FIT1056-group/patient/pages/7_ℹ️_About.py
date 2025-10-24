import streamlit as st
from components.ui import apply_theme, page_header, card

st.set_page_config(page_title="About", page_icon="ℹ️", layout="centered")
apply_theme()
page_header("About CareLog (Patient)", "Scope and key features", "ℹ️")

with card("MVP Scope"):
    st.markdown("""
- Patient authentication with lockout after 3 failed attempts  
- Profile & preferences  
- Daily well-being survey (mood, pain, sleep, meds)  
- Appointment booking (patient-level conflict check)  
- Messaging to care roles (Nurse, Doctor, Medical Staff, Admin)  
- Feedback submission  
- Login history
""")
