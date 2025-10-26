# counselor_name_components/ui.py
import streamlit as st
from counselor_name_app.theme import css_theme

def apply_theme():
    st.markdown(css_theme(), unsafe_allow_html=True)

def require_auth():
    if "auth_user" not in st.session_state:
        with st.sidebar:
            st.subheader("Counselor Login")
            ident = st.text_input("Counselor ID", key="lg_id")
            pwd = st.text_input("Password", type="password", key="lg_pw")
            if st.button("Sign in", type="primary"):
                from counselor_name_app.services.identity import IdentityService
                svc = IdentityService()
                u = svc.login(ident, pwd)
                if u:
                    st.session_state["auth_user"] = u["id"]
                    st.session_state["auth_name"] = u.get("name")
                    st.rerun()
                else:
                    st.error("Invalid credentials or locked account")
        st.stop()

def top_nav(active: str = "Dashboard"):
    """
    Requires a folder literally named 'pages' next to app.py.
    """
    with st.sidebar:
        st.title("🧠 Counselor")
        st.caption(
            f"Signed in as: {st.session_state.get('auth_name','')} "
            f"({st.session_state.get('auth_user','')})"
        )

        # Use icons only; remove emojis from labels to avoid double icons
        st.page_link("pages/1_🏠_Dashboard.py", label="Dashboard", icon="🏠")
        st.page_link("pages/2_🧾_Session_Notes.py", label="Session Notes", icon="📄")
        st.page_link("pages/3_🛡️_Safety_Plans.py", label="Safety Plans", icon="🛡️")
        st.page_link("pages/4_📅_Appointments.py", label="Appointments", icon="📅")
        st.page_link("pages/5_💬_Messages.py", label="Messages", icon="💬")
        st.page_link("pages/6_👤_Profile.py", label="Profile", icon="👤")

        if st.button("Sign out"):
            for k in ("auth_user", "auth_name"):
                st.session_state.pop(k, None)
            st.rerun()
