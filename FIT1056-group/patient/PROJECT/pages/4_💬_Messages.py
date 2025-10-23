import streamlit as st
from components.ui import require_auth, apply_theme, page_header, card
from services.messaging import MessagingService

st.set_page_config(page_title="Messages", page_icon="💬", layout="centered")
apply_theme()
require_auth()

pid = st.session_state.auth_user
svc = MessagingService()

page_header("Messages to Staff", "Reach your care team securely", "💬")

with card("Compose"):
    with st.form("msg_form"):
        recipient_role = st.selectbox("Send to", ["Nurse", "Doctor", "Medical Staff", "Admin"], index=0)
        content = st.text_area("Message")
        submitted = st.form_submit_button("Send")

if submitted:
    if not content.strip():
        st.error("Message cannot be empty.")
    else:
        svc.send(from_patient=pid, to_role=recipient_role, content=content.strip())
        st.success("Message sent.")

with card("My Sent Messages"):
    sent = svc.list_by_patient(pid)
    if not sent:
        st.info("No messages.")
    else:
        for m in reversed(sent[-50:]):
            st.write(f"- {m['ts']} → **{m['to_role']}**: {m['content']}")
