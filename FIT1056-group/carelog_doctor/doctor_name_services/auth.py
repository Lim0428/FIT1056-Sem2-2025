import streamlit as st
from pathlib import Path
import json
from datetime import datetime

LOCKOUT_MAX = 3

# Local, self-contained file paths (no import from data_store to avoid circular import)
DATA_DIR = Path(__file__).resolve().parents[1] / "doctor_name_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCTORS_FILE = DATA_DIR / "doctors.json"

_DEFAULT_DOCTOR = [{
    "id": "doc1",
    "email": "doc@example.com",
    "password": "pass123",
    "safety_q": "pet?",
    "safety_a": "milo",
    "specialty": "General Medicine",
    "qualifications": "MBBS",
    "license_no": "D-001",
    "working_hours": "Mon-Fri 9:00-17:00",
    "contact": "+60-12-345-6789"
}]

def _read_json(path: Path, default):
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return default

def _write_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def ensure_bootstrap_files():
    # Also initialize session state
    _read_json(DOCTORS_FILE, _DEFAULT_DOCTOR)
    if "auth" not in st.session_state:
        st.session_state.auth = {"logged_in": False, "user": None, "fail_count": 0, "locked": False}

def _load_doctors():
    return _read_json(DOCTORS_FILE, _DEFAULT_DOCTOR)

def current_doctor():
    return st.session_state.auth.get("user", {}) or {}

def is_authenticated() -> bool:
    auth = st.session_state.get("auth", {})
    return auth.get("logged_in", False) and not auth.get("locked", False)

def logout():
    st.session_state.auth = {"logged_in": False, "user": None, "fail_count": 0, "locked": False}

def _verify(email_or_phone: str, password: str):
    docs = _load_doctors()
    e = (email_or_phone or "").strip().lower()
    for d in docs:
        if e in (d.get("email","").lower(), d.get("contact","").lower()):
            if d.get("password") == password:
                return d
    return None

def _verify_safety(email_or_phone: str, answer: str):
    docs = _load_doctors()
    e = (email_or_phone or "").strip().lower()
    for d in docs:
        if e in (d.get("email","").lower(), d.get("contact","").lower()):
            return (d.get("safety_a","") or "").strip().lower() == (answer or "").strip().lower()
    return False

def login_form():
    st.title("Sign in")
    if st.session_state.auth.get("locked", False):
        st.error("Account locked after 3 failed attempts. Use safety question to reset your password.")

    email_or_phone = st.text_input("Email or Phone", placeholder="doc@example.com or +60-12-345-6789")
    password = st.text_input("Password", type="password", placeholder="Enter your password")

    col = st.columns(2)
    login_clicked  = col[0].button("Login", use_container_width=True)
    forgot_clicked = col[1].button("Forgot Password", use_container_width=True)

    if login_clicked:
        if st.session_state.auth.get("locked", False):
            st.warning("Account is locked. Please reset via safety question.")
            return
        user = _verify(email_or_phone, password)
        if user:
            st.session_state.auth["logged_in"] = True
            st.session_state.auth["user"] = user
            st.session_state.auth["fail_count"] = 0
            st.success("Welcome.")
            st.rerun()
        else:
            st.session_state.auth["fail_count"] += 1
            if st.session_state.auth["fail_count"] >= LOCKOUT_MAX:
                st.session_state.auth["locked"] = True
            st.error("Invalid credentials.")

    if forgot_clicked:
        with st.form("reset_form"):
            st.write("Answer your safety question to reset.")
            e2 = st.text_input("Email or Phone")
            q = "What is your first pet name?"  # demo label
            st.caption("Stored prompt: " + q)
            a = st.text_input("Your Answer", type="password")
            new_pw = st.text_input("New Password", type="password")
            ok = st.form_submit_button("Reset Password")
            if ok:
                if _verify_safety(e2, a):
                    docs = _load_doctors()
                    e = (e2 or "").strip().lower()
                    for d in docs:
                        if e in (d.get("email","").lower(), d.get("contact","").lower()):
                            d["password"] = new_pw
                    _write_json(DOCTORS_FILE, docs)
                    st.session_state.auth["locked"] = False
                    st.session_state.auth["fail_count"] = 0
                    st.success("Password reset. Please login.")
                else:
                    st.error("Safety answer incorrect.")
