import streamlit as st
from components.ui import apply_desktop_css, page_title
from services.data_store import send_message, list_assigned_patients

st.set_page_config(page_title="Messages", page_icon="💬", layout="wide")
apply_desktop_css()

nurse_id = st.session_state["nurse_id"]
page_title("Secure Messages", "Send updates to doctor / staff / counsellor")

patients = list_assigned_patients(nurse_id)
pid = st.selectbox(
    "Patient",
    [p["id"] for p in patients] if patients else [],
    format_func=lambda pid: next(p["name"] for p in patients if p["id"] == pid) if patients else str(pid),
) if patients else None

to_role = st.selectbox("Send to", ["doctor", "medical_staff", "counsellor"])
text = st.text_input("Message")
urgent = st.checkbox("Flag as urgent")

if st.button("Send"):
    if not pid:
        st.error("Select a patient.")
    elif not text.strip():
        st.error("Enter a message.")
    else:
        msg = send_message(nurse_id, to_role, pid, text.strip(), urgent)
        st.success(f"Sent at {msg['ts']}")
