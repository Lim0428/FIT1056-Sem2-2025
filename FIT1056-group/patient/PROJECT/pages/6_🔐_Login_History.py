import streamlit as st
from components.ui import require_auth, apply_theme, page_header, card
from services.auth import AuthService

st.set_page_config(page_title="Login History", page_icon="🔐", layout="centered")
apply_theme()
require_auth()

pid = st.session_state.auth_user
auth = AuthService()

page_header("Login History", "Security overview of your sessions", "🔐")

with card():
    logs = auth.get_login_history(pid)
    if not logs:
        st.info("No login records yet.")
    else:
        for l in reversed(logs[-50:]):
            ip = l.get("meta", {}).get("ip", "?")
            st.write(f"- {l['ts']} — IP {ip} — {l['status']}")
