import streamlit as st
from components.ui import apply_theme, page_header, card, divider
from app.auth import AuthService, LoginError


st.set_page_config(page_title="CareLog Patient", page_icon="🩺", layout="wide")
apply_theme() 
page_header("CareLog • Patient Portal", "Login or create your patient account", "🩺")

auth = AuthService()

tab_login, tab_register, tab_reset = st.tabs(["Login", "Register", "Reset Password"])

with tab_login:
    with card("Sign in"):
        ident = st.text_input("Email or phone")
        pwd = st.text_input("Password", type="password")
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("Log in"):
                try:
                    user = auth.login(ident, pwd, meta={"via": "patient"})
                    st.session_state["auth_user"] = user["id"]
                    st.session_state["auth_user_obj"] = user
                    st.success("Logged in. Use the sidebar to open pages.")
                    st.toast("Logged in ✓")
                except LoginError as e:
                    st.error(str(e))
        with col2:
            if st.button("Log out"):
                st.session_state.pop("auth_user", None)
                st.session_state.pop("auth_user_obj", None)
                st.info("Logged out.")

with tab_register:
    with card("Create account"):
        r_ident = st.text_input("Email or phone", key="r_ident")
        r_pwd = st.text_input("Password", type="password", key="r_pwd")
        r_sq = st.text_input("Security question", key="r_sq")
        r_sa = st.text_input("Security answer", type="password", key="r_sa")
        r_name = st.text_input("Full name", key="r_name")
        r_dob = st.text_input("Date of birth (YYYY-MM-DD)", key="r_dob")
        if st.button("Register"):
            try:
                uid = auth.register_patient(
                    identifier=r_ident, password=r_pwd,
                    security_q=r_sq, security_a=r_sa,
                    profile={"name": r_name, "dob": r_dob}
                )
                st.success(f"Account created: {uid}. Please login.")
            except Exception as e:
                st.error(str(e))

with tab_reset:
    with card("Reset your password"):
        idf = st.text_input("Email or phone", key="rst_ident")
        if st.button("Get security question"):
            q = auth.get_security_question(idf)
            if q:
                st.session_state["_sq"] = q
            else:
                st.error("Account not found.")
        if "_sq" in st.session_state:
            st.info(f"Security question: {st.session_state['_sq']}")
            ans = st.text_input("Your answer", type="password")
            new_pwd = st.text_input("New password", type="password")
            if st.button("Reset password"):
                ok = auth.reset_password_with_answer(idf, ans, new_pwd)
                if ok:
                    st.success("Password updated. Please login.")
                    st.session_state.pop("_sq", None)
                else:
                    st.error("Incorrect answer.")

divider()
st.caption("Tip: After logging in, use the sidebar Pages to access Profile, Survey, Appointments, Messages, Feedback, and Login History.")
