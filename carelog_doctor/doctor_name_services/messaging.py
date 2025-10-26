from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

# Use current_doctor() to scope threads to the signed-in doctor
from .auth import current_doctor

# ---------- Shared /data folder (same pattern as your DataStore) ----------
ROOT = Path(__file__).resolve().parents[2]   # up to FIT1056-group/
DATA_DIR = ROOT / "data"
MESSAGES_FILE = DATA_DIR / "messages.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)
if not MESSAGES_FILE.exists():
    MESSAGES_FILE.write_text("[]", encoding="utf-8")

# ---------- Small JSON helpers ----------
def _read_json(path: Path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _write_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _now_iso() -> str:
    return datetime.now().isoformat()

# ---------- Public API used by pages/widgets ----------
def list_threads(store=None) -> List[Dict[str, Any]]:
    """
    Return threads for the current doctor (status open/resolved).
    Each thread:
      { id, patient_id, doctor_id, name?, status, updated_at, messages: [...] }
    """
    rows = _read_json(MESSAGES_FILE, [])
    me = current_doctor() or {}
    me_id = me.get("id")

    # Normalize & filter to this doctor
    norm: List[Dict[str, Any]] = []
    for t in rows:
        if not isinstance(t, dict):
            continue
        if me_id and t.get("doctor_id") != me_id:
            continue
        msgs = t.get("messages") or []
        # ensure updated_at exists
        updated = t.get("updated_at")
        if not updated and msgs:
            updated = msgs[-1].get("timestamp")
        if not updated:
            updated = _now_iso()
        tt = {
            "id": t.get("id"),
            "patient_id": t.get("patient_id"),
            "doctor_id": t.get("doctor_id"),
            "name": t.get("name"),                # optional (patient name)
            "status": t.get("status", "open"),
            "updated_at": updated,
            "messages": msgs,
        }
        norm.append(tt)

    # Newest first by updated_at
    def _parse(ts: str):
        try:
            return datetime.fromisoformat(str(ts).replace("Z", ""))
        except Exception:
            return datetime.min
    norm.sort(key=lambda x: _parse(x["updated_at"]), reverse=True)
    return norm

def get_thread(store, thread_id: str) -> Optional[Dict[str, Any]]:
    if not thread_id:
        return None
    rows = _read_json(MESSAGES_FILE, [])
    for t in rows:
        if isinstance(t, dict) and str(t.get("id")) == str(thread_id):
            return t
    return None

def add_message(store, thread_id: str, sender_role: str, text: str) -> bool:
    """
    Append a message to a thread and update updated_at.
    sender_role: "doctor" | "patient"
    """
    rows = _read_json(MESSAGES_FILE, [])
    changed = False
    for t in rows:
        if not isinstance(t, dict):
            continue
        if str(t.get("id")) != str(thread_id):
            continue
        msgs = list(t.get("messages") or [])
        msgs.append({
            "id": f"m{len(msgs)+1}",
            "sender_role": sender_role,
            "text": text,
            "timestamp": _now_iso(),
        })
        t["messages"] = msgs
        t["updated_at"] = _now_iso()
        # If it was resolved, re-open on new message from either side (optional)
        if t.get("status") == "resolved":
            t["status"] = "open"
        changed = True
        break

    if changed:
        _write_json(MESSAGES_FILE, rows)
    return changed

def mark_resolved(store, thread_id: str) -> bool:
    """Set a thread's status to resolved."""
    rows = _read_json(MESSAGES_FILE, [])
    changed = False
    for t in rows:
        if not isinstance(t, dict):
            continue
        if str(t.get("id")) != str(thread_id):
            continue
        t["status"] = "resolved"
        t["updated_at"] = _now_iso()
        changed = True
        break

    if changed:
        _write_json(MESSAGES_FILE, rows)
    return changed
