# admin_name_utils/auth.py
import streamlit as st
from datetime import datetime
from admin_name_utils.doctors_io import list_doctors, save_doctors, upsert_doctor, delete_doctor

from admin_name_utils.storage import (
    load_db, save_db, bootstrap_store,
    load_admins, save_admins, admins_file_path
)

MAX_ATTEMPTS = 3

# ---------- helpers ----------
def _record_attempt(email: str, ok: bool):
    db = load_db()
    la = db.get("login_attempts", {})
    rec = la.get(email, {"fails": 0})
    rec["fails"] = 0 if ok else rec.get("fails", 0) + 1
    la[email] = rec
    db["login_attempts"] = la
    save_db(db)
    return rec["fails"]

def _seed_default_admin_if_needed() -> bool:
    """
    Ensure data/admins.json exists and has at least one admin.
    Returns True if we created/seeded the file.
    """
    bootstrap_store()
    admins = load_admins()
    if admins:
        return False
    admins = [{
        "id": 1,
        "name": "Admin",
        "email": "admin@carelog.local",
        "role": "admin",
        "locked": False,
        "pwd": "admin123"
    }]
    save_admins(admins)
    return True

# ---------- required by app.py ----------
def ensure_auth(required_role: str = "admin") -> bool:
    """True if a user is logged in and has the required role."""
    u = st.session_state.get("user")
    return bool(u and u.get("role") == required_role)

def logout_button():
    if st.button("Logout", type="secondary", use_container_width=True):
        st.session_state.pop("user", None)
        st.rerun()

# ---------- login panel ----------
def login_panel():
    # Greeting
    hr = datetime.now().hour
    if 5 <= hr < 12:
        emoji, part = "☀️", "morning"
    elif 12 <= hr < 18:
        emoji, part = "🌤️", "afternoon"
    else:
        emoji, part = "🌙", "evening"
    st.markdown(
        f'<div style="text-align:center;margin:10px 0 18px;">'
        f'<span style="padding:6px 12px;border:1px solid rgba(255,255,255,.12);'
        f'border-radius:999px;background:rgba(255,255,255,.04);">'
        f'{emoji} Good {part}! Welcome to CareLog Admin</span></div>',
        unsafe_allow_html=True,
    )

    # First-time seed
    seeded = _seed_default_admin_if_needed()
    if seeded:
        st.info("Created default admin in data/admins.json (admin@carelog.local / admin123).")

    # Form-based login
    st.markdown('<div style="max-width:520px;margin:0 auto;">', unsafe_allow_html=True)
    st.markdown("## Sign in")
    st.caption("Admins are stored in `data/admins.json`.")

    remembered_email = st.session_state.get("_remembered_email", "admin@carelog.local")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", value=remembered_email, autocomplete="email")
        show = st.toggle("Show password", value=False)
        pwd = st.text_input("Password", type=("default" if show else "password"))
        remember = st.checkbox("Remember me", value=True)
        submitted = st.form_submit_button("Log in", use_container_width=True)

    # Lockout progress
    la = load_db().get("login_attempts", {})
    fails = la.get(email, {}).get("fails", 0)
    ratio = min(fails / MAX_ATTEMPTS, 1.0)
    st.progress(ratio, text=f"Login protection: {fails}/{MAX_ATTEMPTS} failed attempts")

    # Inline unlock/reset (only if we can find the admin record)
    admins = load_admins()
    user_now = next((u for u in admins if u["email"].lower() == (email or "").lower()), None)
    if user_now and user_now.get("locked"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Unlock account", use_container_width=True):
                user_now["locked"] = False
                save_admins(admins)
                db = load_db()
                la = db.get("login_attempts", {})
                la[email] = {"fails": 0}
                db["login_attempts"] = la
                save_db(db)
                st.success("Unlocked. Please log in.")
                st.rerun()
        with c2:
            if st.button("Reset attempts", use_container_width=True):
                db = load_db()
                la = db.get("login_attempts", {})
                la[email] = {"fails": 0}
                db["login_attempts"] = la
                save_db(db)
                st.info("Attempts reset.")
                st.rerun()

    # Submit handling
    if submitted:
        if not email.strip():
            st.error("Please enter your email.")
        elif not pwd:
            st.error("Please enter your password.")
        else:
            admins = load_admins()
            user = next((u for u in admins if u["email"].lower() == email.lower()), None)

            if not user:
                st.error("Admin account not found (data/admins.json).")
            elif user.get("locked"):
                st.error("Account is locked. Use “Unlock account”.")
            elif pwd == user.get("pwd"):
                if remember:
                    st.session_state["_remembered_email"] = email
                _record_attempt(email, ok=True)  # clears fails
                st.session_state["user"] = {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": "admin",
                }
                st.success("Welcome!")
                st.rerun()
            else:
                fails = _record_attempt(email, ok=False)
                if fails >= MAX_ATTEMPTS:
                    user["locked"] = True
                    save_admins(admins)
                    st.error("Account locked due to 3 failed attempts.")
                else:
                    st.error(f"Incorrect password. {MAX_ATTEMPTS - fails} attempt(s) left.")

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    p = admins_file_path()
    st.caption(f"Admin file: `{p}`")
    st.markdown('</div>', unsafe_allow_html=True)
