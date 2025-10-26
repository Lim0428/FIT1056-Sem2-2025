# tests/conftest.py
import sys
from pathlib import Path
import types
import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture(autouse=True)
def fresh_streamlit(monkeypatch):
    """Provide a fresh, dict-like session_state for each test."""
    import streamlit as st
    st.session_state = {}
    # Avoid accidentally calling st functions that would need a runtime
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(st, "button",   lambda *a, **k: False, raising=False)
    monkeypatch.setattr(st, "toast",    lambda *a, **k: None, raising=False)
    return st

@pytest.fixture()
def fake_db(monkeypatch):
    """In-memory DB and patched load_db/save_db."""
    storage = {"users": [], "appointments": [], "patients": [], "rooms": [], "invoices": []}

    # Patch admin_name_utils.storage
    from admin_name_utils import storage as real_storage

    def load_db():
        return storage

    def save_db(db):
        storage.clear()
        storage.update(db)

    monkeypatch.setattr(real_storage, "load_db", load_db, raising=True)
    monkeypatch.setattr(real_storage, "save_db", save_db, raising=True)

    # Also patch modules that import these at module scope (common in your code)
    monkeypatch.setenv("PYTEST_FAKE_DB", "1")
    return storage
