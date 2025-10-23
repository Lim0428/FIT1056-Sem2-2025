import streamlit as st
from datetime import date
from services.auth import AuthService, LoginError
from components.ui import divider, apply_theme, page_header, card

st.set_page_config(page_title="CareLog (Patient Portal)", page_icon="🩺", layout="centered")

def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

apply_theme()  # <<< NEW

auth = AuthService()
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

page_header("CareLog — Patient Portal (Home)", "Secure patient access & daily tools", "🩺")

if st.session_state.auth_user:
    st.success(f"You are logged in as: {st.session_state.auth_user}")
    if st.button("Log out"):
        st.session_state.auth_user = None
        _rerun()
    divider()
    with card("Navigation"):
        st.write("Use the left sidebar to open pages: **Profile & Preferences**, **Daily Survey**, **Appointments**, **Messages**, **Feedback**, **Login History**, **About**.")
else:
    tab_login, tab_register, tab_reset = st.tabs(["Login", "Register", "Reset Password"])

    with tab_login:
        page_header("Login", "", "🔐")
        with card():
            with st.form("login_form"):
                identifier = st.text_input("Email or phone", placeholder="someone@example.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log in")
            if submitted:
                try:
                    u = auth.login(identifier, password, meta={"ip": "127.0.0.1"})
                    st.session_state.auth_user = u["id"]
                    st.success("Logged in successfully.")
                    _rerun()
                except LoginError as e:
                    st.error(str(e))

    with tab_register:
        page_header("Create Account", "", "🆕")
        with card():
            with st.form("register_form"):
                email_or_phone = st.text_input("Email or phone *")
                password = st.text_input("Password *", type="password")
                confirm = st.text_input("Confirm password *", type="password")
                sec_q = st.text_input("Security question *", placeholder="e.g., Your first school?")
                sec_a = st.text_input("Security answer *")
                full_name = st.text_input("Full name *")
                dob = st.date_input("Date of birth", value=date(1990, 1, 1))
                submit_reg = st.form_submit_button("Create account")
            if submit_reg:
                if not email_or_phone or not password or not confirm or not sec_q or not sec_a or not full_name:
                    st.error("Please fill all required fields.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    try:
                        uid = auth.register_patient(
                            identifier=email_or_phone,
                            password=password,
                            security_q=sec_q,
                            security_a=sec_a,
                            profile={"name": full_name, "dob": str(dob)}
                        )
                        st.success(f"Account created. Your user ID is {uid}. You can now log in.")
                    except ValueError as e:
                        st.error(str(e))

    with tab_reset:
        page_header("Reset Password", "Answer the security question to reset", "♻️")
        with card():
            with st.form("reset_form"):
                ident = st.text_input("Email or phone")
                q = ""
                if ident:
                    q = auth.get_security_question(ident) or ""
                if q:
                    st.caption(f"Security question: {q}")
                answer = st.text_input("Answer")
                newpwd = st.text_input("New password", type="password")
                submitted_reset = st.form_submit_button("Reset password")
            if submitted_reset:
                ok = auth.reset_password_with_answer(ident, answer, newpwd)
                if ok:
                    st.success("Password reset. Please log in.")
                else:
                    st.error("Reset failed. Check identifier and answer.")

divider()
st.caption("Tip: the **pages/** folder contains the rest of the functionality. Use Streamlit’s sidebar to navigate.")
