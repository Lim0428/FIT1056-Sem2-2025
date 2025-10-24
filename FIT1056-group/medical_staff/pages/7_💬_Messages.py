# medical_staff/pages/7_💬_Messages.py
import streamlit as st
from components.ui import apply_theme, page_header, card
from components.staff_shared import pick_staff_and_patient
from app.medical_staff import MedicalStaffService

st.set_page_config(page_title="Messages", page_icon="💬", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Messages", "Two-way messages with patient.", "💬")

staff_id, patient = pick_staff_and_patient("msg_pick")
if not patient:
    st.stop()
pid = patient["id"]

with card("Send a message"):
    out_text = st.text_input("Write a message", "", key=f"msg_out_{pid}")
    if st.button("📨 Send", type="primary", key=f"msg_send_{pid}"):
        if out_text.strip():
            svc.send_message_to_patient(staff_id, pid, out_text)
            st.success("Sent.")
        else:
            st.error("Type your message before sending.")

with card("Conversation"):
    msgs = svc.list_messages_for_patient(pid, limit=100)
    if not msgs: st.caption("No messages yet.")
    else:
        for m in msgs:
            who = "👩‍⚕️ Staff" if m.get("from_role") == "staff" else "🧑 Patient"
            st.write(f"{who} — **{m.get('timestamp','')}**: {m.get('text','')}")
