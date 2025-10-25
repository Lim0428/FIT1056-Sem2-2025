# doctor_name_services/messaging.py
from __future__ import annotations
from datetime import datetime
from .data_store import FILES, _read_json, _write_json
from doctor_name_services.auth import current_doctor

def _now_iso(): return datetime.now().isoformat()

def list_threads(store=None):
    rows = _read_json(FILES["messages"], [])
    me = current_doctor()
    return [t for t in rows if t.get("doctor_id")==me.get("id")] if me else rows

def get_thread(store, tid):
    rows = _read_json(FILES["messages"], [])
    for t in rows:
        if t.get("id")==tid: return t
    return None

def _save_threads(rows):
    _write_json(FILES["messages"], rows)

def add_message(store, tid, sender_role, text):
    rows = _read_json(FILES["messages"], [])
    for t in rows:
        if t.get("id")==tid:
            t.setdefault("messages", []).append({
                "sender_role": sender_role,
                "text": text,
                "timestamp": _now_iso()
            })
            t["updated_at"] = _now_iso()
            if t.get("status")=="resolved":
                t["status"]="open"
            break
    _save_threads(rows)

def mark_resolved(store, tid):
    rows = _read_json(FILES["messages"], [])
    for t in rows:
        if t.get("id")==tid:
            t["status"]="resolved"; t["updated_at"]=_now_iso(); break
    _save_threads(rows)
