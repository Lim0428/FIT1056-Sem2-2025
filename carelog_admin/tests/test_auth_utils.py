# tests/test_auth_utils.py
import streamlit as st
from admin_name_utils.auth import _record_attempt, _seed_default_admin, ensure_auth
from admin_name_utils.storage import load_db

def test_seed_default_admin(fake_db):
    db = load_db()
    assert db["users"] == []
    created = _seed_default_admin()
    assert created is True
    assert len(load_db()["users"]) == 1
    # second call no-op
    created2 = _seed_default_admin()
    assert created2 is False

def test_record_attempt_and_reset(fake_db):
    email = "user@example.com"
    n1 = _record_attempt(email, ok=False)
    n2 = _record_attempt(email, ok=False)
    assert (n1, n2) == (1, 2)
    n3 = _record_attempt(email, ok=True)  # resets
    assert n3 == 0

def test_ensure_auth_checks_role(monkeypatch):
    st.session_state = {"user": {"role": "admin"}}
    assert ensure_auth("admin") is True
    assert ensure_auth("doctor") is False
