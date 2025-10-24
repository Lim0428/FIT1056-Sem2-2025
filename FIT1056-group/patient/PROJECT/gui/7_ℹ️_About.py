import streamlit as st
from components.ui import apply_theme, page_header, card

st.set_page_config(page_title="About", page_icon="ℹ️", layout="centered")
apply_theme()

page_header("About CareLog MVP", "Patient-centered features in a compact demo", "ℹ️")

with card():
    st.write(
        """
This MVP demonstrates the **patient** functional requirements:

- Registration & login (security question), **3-strike lockout**, and login history  
- Profile & preferences (food, language, nurse gender), medical details, emergency contact  
- Daily survey (mood, pain, sleep, medication) with history  
- Appointment booking (basic conflict prevention)  
- Messages to staff; feedback submission  

**Out of scope (placeholders):** reminders/calendar view, advanced privacy matrix, MFA across all routes.
"""
    )
