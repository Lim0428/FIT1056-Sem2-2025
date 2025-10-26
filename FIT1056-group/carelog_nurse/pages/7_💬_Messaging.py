# carelog_nurse/pages/7_💬_Messaging.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
import streamlit as st

from components.ui import apply_theme, page_header

# ---------- Paths ----------
ROOT = Path(__file__).resolve().parents[2]     # <repo root>
DATA_DIR = ROOT / "data"
CHAT_PATH = DATA_DIR / "admin_nurse_chat.json" # <-- the chat you said to connect
ADMINS_PATH = DATA_DIR / "admins.json"
PATIENTS_PATH = DATA_DIR / "patients.json"
NURSE_CTX_PATH = DATA_DIR / "carelog_nurse.json"  # optional: to resolve nurse numeric id

# ---------- Utilities ----------
def _load_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
            return obj if obj is not None else default
    except Exception:
        return default

def _save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def _to_list(obj):
    """Normalize dict-or-list JSON to a list (keeps dict values)."""
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        return [obj[k] for k in sorted(obj.keys())]
    return []

def _now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _get_current_nurse_numeric_id() -> int:
    """
    Try to derive a numeric sender id for the nurse.
    Fallback to 5 if we can't resolve it (your sample uses 1↔5).
    """
    ctx = _load_json(NURSE_CTX_PATH, {})
    for key in ("user_id", "numeric_id", "id"):
        v = ctx.get(key)
        try:
            if v is not None:
                return int(v)
        except Exception:
            pass
    return 5

def _admin_choices():
    admins = _to_list(_load_json(ADMINS_PATH, []))
    if not admins:
        return [(1, "Admin")]
    choices = []
    for a in admins:
        aid = a.get("id")
        name = a.get("name") or a.get("full_name") or f"Admin {aid}"
        try:
            aid = int(aid)
        except Exception:
            continue
        choices.append((aid, name))
    return choices or [(1, "Admin")]

def _patient_choices():
    pts = _to_list(_load_json(PATIENTS_PATH, []))
    items = []
    for p in pts:
        if not isinstance(p, dict):
            continue
        pid = p.get("id") or p.get("patient_id")
        if not pid:
            continue
        label = f'{pid} — {p.get("name") or p.get("full_name") or ""}'.strip(" —")
        items.append((pid, label))
    return [("", "— None —")] + items

# ---- Robust chat reader ----
def _read_chat_robust(path: Path) -> list[dict]:
    """Accepts:
       - Proper JSON array
       - Dict with 'messages'
       - Single object
       - A file containing multiple JSON objects separated by commas without [].
    """
    if not path.exists() or path.stat().st_size == 0:
        return []
    raw = path.read_text(encoding="utf-8").strip()
    if raw in {"", "[]", "{}", "null"}:
        return []
    # First try normal JSON
    try:
        obj = json.loads(raw)
    except Exception:
        # Try to wrap loose objects into an array
        try:
            fixed = raw.strip().rstrip(",")
            if not fixed.startswith("["):
                fixed = "[" + fixed + "]"
            obj = json.loads(fixed)
        except Exception:
            return []
    # Normalize to list[dict]
    out = []
    if isinstance(obj, list):
        out = [x for x in obj if isinstance(x, dict)]
    elif isinstance(obj, dict):
        if isinstance(obj.get("messages"), list):
            out = [x for x in obj["messages"] if isinstance(x, dict)]
        else:
            out = [obj]
    else:
        out = []
    # Ensure minimal keys
    cleaned = []
    for m in out:
        if isinstance(m, dict) and ("from_id" in m or "to_id" in m or "text" in m):
            cleaned.append(m)
    return cleaned

# ---------- Page ----------
st.set_page_config(page_title="Messaging", page_icon="💬", layout="wide")
apply_theme()
page_header("Messaging", "Chat with Admin", "💬")

# Current nurse numeric id (for from_id)
NURSE_NUM_ID = _get_current_nurse_numeric_id()

# Load data
chat = _read_chat_robust(CHAT_PATH)
admin_opts = _admin_choices()
patient_opts = _patient_choices()

# ---------- Send message (FORM with submit button) ----------
st.markdown("### New message")
with st.form("msg_form", clear_on_submit=True):
    c1, c2 = st.columns([2, 1])
    with c1:
        to_admin = st.selectbox(
            "Recipient (Admin)",
            options=[name for (_id, name) in admin_opts],
            index=0,
            key="msg_to_admin"
        )
    with c2:
        patient_choice = st.selectbox(
            "Related patient (optional)",
            options=[label for (_pid, label) in patient_opts],
            index=0,
            key="msg_patient"
        )

    text = st.text_area("Message", placeholder="Write your message…", height=120, key="msg_text")
    urgent = st.checkbox("Mark as urgent", key="msg_urgent")

    submitted = st.form_submit_button("Send")

if submitted:
    to_id = next((aid for (aid, name) in admin_opts if name == to_admin), 1)
    related_pid = next((pid for (pid, label) in patient_opts if label == patient_choice), "")
    if text.strip():
        next_id = (max([m.get("id", 0) for m in chat], default=0) + 1) if chat else 1
        msg = {
            "id": next_id,
            "from_id": NURSE_NUM_ID,
            "to_id": to_id,
            "text": text.strip() + (" [URGENT]" if urgent else ""),
            "ts": _now_iso(),
            "read": False
        }
        if related_pid:
            msg["patient_id"] = related_pid
        chat.append(msg)
        _save_json(CHAT_PATH, chat)
        st.success("Message sent.")
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()

# ---------- Thread view ----------
st.markdown("### Admin ↔ Nurse thread")

if not chat:
    st.info("No messages yet.")
else:
    # Newest first
    chat_sorted = sorted(chat, key=lambda m: m.get("ts",""), reverse=True)
    for m in chat_sorted[:200]:
        mine = (m.get("from_id") == NURSE_NUM_ID)
        who = "You" if mine else f"Admin #{m.get('from_id')}"
        align = "flex-end" if mine else "flex-start"
        bg = "#17304d" if mine else "#15233a"
        brd = "#28507f" if mine else "#243c63"
        txt = (m.get("text") or "").replace("\n", "<br/>")
        pid = m.get("patient_id")
        meta = f'{m.get("ts","")}{" • Patient: "+pid if pid else ""}{" • unread" if not m.get("read") else ""}'

        st.markdown(
            f"""
            <div style="display:flex; justify-content:{align}; margin:8px 0;">
              <div style="
                   max-width: 72%;
                   background:{bg};
                   border:1px solid {brd};
                   color:#e6edf3;
                   padding:10px 12px;
                   border-radius:12px;">
                <div style="font-weight:700; margin-bottom:4px;">{who}</div>
                <div style="line-height:1.4;">{txt}</div>
                <div style="color:#9fb0c3; font-size:12px; margin-top:6px;">{meta}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------- Mark all as read ----------
colA, colB = st.columns([1,5])
if colA.button("Mark all as read", key="mark_all_read"):
    any_change = False
    for m in chat:
        if not m.get("read"):
            m["read"] = True
            any_change = True
    if any_change:
        _save_json(CHAT_PATH, chat)
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()
    else:
        st.caption("All messages already read.")
