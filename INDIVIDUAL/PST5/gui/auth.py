# gui/auth.py
from typing import Optional, Dict, List
import streamlit as st
from streamlit_autorefresh import st_autorefresh



ROLE_PAGES = {
    "student": ["Check-in", "Submit Feedback", "My Courses", "My Grades"],

    "teacher": ["Roster", "Lessons", "Courses", "Grades", "Feedback", "Courses List"],

    # receptionist: can manage people and money
    "receptionist": [
        "Daily Roster", "Student Enrollment","Register Student", "Attendance", "Finance", "Student Feedback", "Register Teacher", "Attendance",
        "Directory",
    ],

    # schedule manager: operations + high-level reports
    "schedule_manager": [
        "Courses", "Lessons",
        "Directory"
    ],
}

def allowed_pages_for(user: Dict) -> List[str]:
    return list(ROLE_PAGES.get(user["role"], []))

def logout_button():
    if st.button("Log out"):
        for k in ("user", "nav"):
            st.session_state.pop(k, None)
        st.rerun()  

def change_password_ui(manager, user):
    with st.expander("Change password", expanded=False):
        st.caption("Update your password. You must enter your current password.")
        col1, col2 = st.columns(2)
        with col1:
            old = st.text_input("Current password", type="password", key="pw_old")
            new = st.text_input("New password", type="password", key="pw_new")
        with col2:
            confirm = st.text_input("Confirm new password", type="password", key="pw_new2")
            st.write("")  # spacer
            if st.button("Update password"):
                if not new:
                    st.warning("New password cannot be empty.")
                elif new != confirm:
                    st.warning("New password and confirmation do not match.")
                else:
                    ok = manager.change_password(user["role"], user["user_id"], old, new)
                    if ok:
                        st.success("Password updated.")
                    else:
                        st.error("Password change failed. Check your current password.")


def login_ui(manager=None) -> Optional[Dict]:
    # Already logged in -> don't show the form
    existing = st.session_state.get("user")
    if existing:
        return existing

    st.subheader("Music School Management System - Login")

    # --- read any previous inputs (so we can compute lock BEFORE drawing the form)
    role_key = "login_role"
    id_key   = "login_id"
    pw_key   = "login_pw"
    pre_role = st.session_state.get(role_key, "student")
    pre_user = st.session_state.get(id_key, "")

    # --- compute lock state early and (IMPORTANT) trigger autorefresh OUTSIDE the form
    pre_locked, pre_secs = (False, 0)
    if manager and pre_user:
        if hasattr(manager, "is_locked"):
            pre_locked, pre_secs = manager.is_locked(pre_role, pre_user)
        # autorefresh must be outside the form or it won't rerun
        if pre_locked:
            st_autorefresh(interval=1000, key=f"lock-refresh::{pre_role}::{pre_user}")

    # --- now draw the form (normal)
    with st.form("login_form", clear_on_submit=False):
        role = st.selectbox("Role",
                            ["student", "teacher", "receptionist", "schedule_manager"],
                            index=["student","teacher","receptionist","schedule_manager"].index(pre_role)
                            if pre_role in {"student","teacher","receptionist","schedule_manager"} else 0,
                            key=role_key)

        user_id = st.text_input("ID",
                                help="Students/Teachers: numeric ID. Staff: r001 / s001 by default.",
                                value=pre_user, key=id_key)

        password = st.text_input("Password", type="password", key=pw_key)

        # Compute lock/attempts for messaging (safe to reuse the pre_* values)
        locked, secs = pre_locked, pre_secs
        attempts_left = None
        if manager and user_id and not locked and hasattr(manager, "remaining_attempts"):
            attempts_left = manager.remaining_attempts(role, user_id)

        # Show exactly one message here
        if locked:
            st.error(f"Too many failed attempts. This account is locked for {secs} more seconds.")
        elif attempts_left is not None:
            st.caption(f"Attempts remaining before 1-minute lock: {attempts_left}")

        submitted = st.form_submit_button("Sign in", disabled=locked)

    # If not submitted (or locked), stop here. No extra banners.
    if not submitted:
        return None

    # Basic checks
    if not user_id or not password:
        return None
    if role in {"student", "teacher"} and not user_id.isdigit():
        return None

    # Verify
    user = manager.verify_login(role, user_id, password) if (manager and hasattr(manager, "verify_login")) else None
    if user:
        st.session_state["user"] = user
        st.rerun()
        return user

    # On failure, do nothing; next rerun shows attempts/lock in the form.
    st.rerun()