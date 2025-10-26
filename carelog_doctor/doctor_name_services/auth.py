# doctor_name_services/auth.py
from __future__ import annotations
import json
from pathlib import Path
import streamlit as st
from .data_store import FILES, _read_json, _write_json

def ensure_bootstrap_files():
    # create baseline doctors.json if missing
    rows = _read_json(FILES["doctors"], [])
    if not rows:
        rows = [{
            "id": "doc1",
            "email": "doc@example.com",
            "password": "pass123",
            "safety_q": "pet?", "safety_a": "milo",
            "specialty": "General Medicine", "qualifications": "MBBS",
            "license_no": "D-001", "working_hours": "Mon–Fri 9:00–17:00",
            "contact": "+60-12-345-6789"
        }]
        _write_json(FILES["doctors"], rows)
    _read_json(FILES["patients"], [])
    _read_json(FILES["appointments"], [])
    _read_json(FILES["messages"], [])
    _read_json(FILES["encounters"], [])

def is_authenticated() -> bool:
    return bool(st.session_state.get("auth", {}).get("user"))

def current_doctor() -> dict:
    return st.session_state.get("auth", {}).get("user", {}) if is_authenticated() else {}

def login_form():
    st.markdown("### Login")
    with st.form("login"):
        email = st.text_input("Email", value="doc@example.com")
        pw = st.text_input("Password", type="password", value="pass123")
        ok = st.form_submit_button("Login")
        if ok:
            docs = _read_json(FILES["doctors"], [])
            for d in docs:
                if d.get("email")==email and d.get("password")==pw:
                    st.session_state["auth"] = {"user": d}
                    st.success("Logged in.")
                    st.rerun()
            st.error("Invalid credentials.")
    st.caption("Default: doc@example.com / pass123")

def logout():
    st.session_state.pop("auth", None)