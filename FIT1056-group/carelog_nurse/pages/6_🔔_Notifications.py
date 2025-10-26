# nurse/pages/6_🔔_Notifications.py
import streamlit as st
from components.ui import apply_theme, page_header
from app.nurse_service import NurseService

st.set_page_config(page_title="Notifications", page_icon="🔔", layout="wide")
apply_theme()
page_header("Notifications", "Doctor order updates & patient calls", "🔔")

svc = NurseService()
rows = svc.list_notifications()

for n in rows:
    cols = st.columns([4,2,1])
    cols[0].write(f'**{n["text"]}**')
    cols[1].write(f'{n["created_at"]} · {n["status"]}')
    if n["status"] != "read" and cols[2].button("Acknowledge", key=n["id"]):
        svc.ack_notification(n["id"])
        st.success("Acknowledged.")
