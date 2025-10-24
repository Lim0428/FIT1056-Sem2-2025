# patient/pages/4_💬_Messages.py
import streamlit as st
from components.ui import apply_theme, page_header, card, require_auth
from app.messaging import MessagingService
# Use a non-conflicting alias for translation
try:
    from app.i18n import _ as t, translate_series
except Exception:
    # Fallback if i18n not present or misconfigured
    t = lambda s: s
    def translate_series(seq): return list(seq)

st.set_page_config(page_title=t("Messages"), page_icon="💬", layout="centered")
apply_theme()
require_auth()
page_header(t("Messages"), t("Send a message to the care team"), "💬")

svc = MessagingService()
pid = st.session_state["auth_user"]

ROLE_CHOICES = [
    ("Nurse", "Nurse"),
    ("Doctor", "Doctor"),
    ("Medical Staff", "Medical Staff"),
    ("Admin", "Admin"),
]

with card(t("New message")):
    display_options = [t(label) for (_, label) in ROLE_CHOICES]
    role_index = st.selectbox(
        t("Send to"),
        options=list(range(len(display_options))),
        format_func=lambda i: display_options[i],
        key="msg_role_select",
    )
    to_role = ROLE_CHOICES[role_index][0]

    content = st.text_area(t("Your message"), key="msg_body")
    if st.button(t("Send"), key="msg_send"):
        if content.strip():
            svc.send(pid, to_role, content.strip())
            st.success(t("Sent."))
            st.rerun()
        else:
            st.error(t("Message cannot be empty."))

with card(t("Sent")):
    items = list(reversed(svc.list_by_patient(pid)))
    if not items:
        st.info(t("No messages yet."))
    else:
        for m in items:
            translated = translate_series([m.get("content", "")])[0]
            to_role_disp = t(m.get("to_role", ""))
            st.write(f"• **{m.get('ts','')}** → {to_role_disp}: {translated}")
