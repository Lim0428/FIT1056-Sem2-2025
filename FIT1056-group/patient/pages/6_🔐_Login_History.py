import streamlit as st
from components.ui import apply_theme, page_header, card, require_auth
from app.auth import AuthService

st.set_page_config(page_title="Login History", page_icon="🔐", layout="centered")
apply_theme()
require_auth()
page_header("Login History", "Recent authentication events", "🔐")

auth = AuthService()
pid = st.session_state["auth_user"]

with card("Recent"):
    items = list(reversed(auth.get_login_history(pid)))[:50]
    if not items:
        st.info("No history yet.")
    else:
        for e in items:
            st.write(f"• **{e['ts']}** — {e['status']}")
