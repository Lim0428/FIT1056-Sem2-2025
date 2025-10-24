from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

APP_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = APP_DIR / "data.json"
AUDIT_LOG = APP_DIR / "audit.log"

def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def read_data() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        return {
            "nurses": [],
            "patients": [],
            "assignments": [],
            "mar": [],
            "vitals": [],
            "notes": [],
            "tasks": [],
            "messages": [],
            "notifications": [],
        }
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def write_data(data: Dict[str, Any]) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def audit(event: str, actor_id: str, subject: str, details: Dict[str, Any]) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": _now_iso(),
            "event": event,
            "actor": actor_id,
            "subject": subject,
            "details": details
        }) + "\n")

def list_assigned_patients(nurse_id: str) -> List[Dict[str, Any]]:
    d = read_data()
    ids = {a["patient_id"] for a in d.get("assignments", []) if a["nurse_id"] == nurse_id}
    return [p for p in d.get("patients", []) if p["id"] in ids]

def check_access(nurse_id: str, patient_id: str) -> bool:
    d = read_data()
    return any(a["nurse_id"] == nurse_id and a["patient_id"] == patient_id for a in d.get("assignments", []))

def add_mar_entry(nurse_id: str, patient_id: str, drug: str, dose: str, route: str, when_iso: Optional[str] = None) -> Dict[str, Any]:
    if not check_access(nurse_id, patient_id):
        audit("access_denied", nurse_id, f"patient:{patient_id}", {"module": "mar"})
        raise PermissionError("You are not assigned to this patient.")
    d = read_data()
    entry = {
        "id": f"mar_{len(d.get('mar', [])) + 1}",
        "ts": when_iso or _now_iso(),
        "nurse_id": nurse_id,
        "patient_id": patient_id,
        "drug": drug,
        "dose": dose,
        "route": route,
    }
    d.setdefault("mar", []).append(entry)
    write_data(d)
    audit("mar_add", nurse_id, f"patient:{patient_id}", {"drug": drug, "dose": dose, "route": route})
    return entry

def add_vitals(nurse_id: str, patient_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
    if not check_access(nurse_id, patient_id):
        audit("access_denied", nurse_id, f"patient:{patient_id}", {"module": "vitals"})
        raise PermissionError("You are not assigned to this patient.")
    d = read_data()
    entry = {
        "id": f"vitals_{len(d.get('vitals', [])) + 1}",
        "ts": _now_iso(),
        "nurse_id": nurse_id,
        "patient_id": patient_id,
        "values": values,
    }
    d.setdefault("vitals", []).append(entry)
    write_data(d)
    audit("vitals_add", nurse_id, f"patient:{patient_id}", {"values": values})
    return entry

def add_note(nurse_id: str, patient_id: str, text: str) -> Dict[str, Any]:
    if not check_access(nurse_id, patient_id):
        audit("access_denied", nurse_id, f"patient:{patient_id}", {"module": "notes"})
        raise PermissionError("You are not assigned to this patient.")
    d = read_data()
    entry = {
        "id": f"note_{len(d.get('notes', [])) + 1}",
        "ts": _now_iso(),
        "nurse_id": nurse_id,
        "patient_id": patient_id,
        "text": text,
    }
    d.setdefault("notes", []).append(entry)
    write_data(d)
    audit("note_add", nurse_id, f"patient:{patient_id}", {"len": len(text)})
    return entry

def list_timeline(patient_id: str) -> List[Dict[str, Any]]:
    d = read_data()
    items: List[Dict[str, Any]] = []
    for col, kind in [("vitals", "vitals"), ("notes", "note"), ("mar", "mar")]:
        for e in d.get(col, []):
            if e["patient_id"] == patient_id:
                x = dict(e); x["_kind"] = kind; items.append(x)
    items.sort(key=lambda x: x["ts"], reverse=True)
    return items

def list_tasks(nurse_id: str) -> List[Dict[str, Any]]:
    d = read_data()
    rows = [t for t in d.get("tasks", []) if t["nurse_id"] == nurse_id]
    rows.sort(key=lambda r: (r.get("completed", False), r.get("due", "")))
    return rows

def complete_task(task_id: str, nurse_id: str) -> None:
    d = read_data()
    ok = False
    for t in d.get("tasks", []):
        if t["id"] == task_id and t["nurse_id"] == nurse_id:
            t["completed"] = True
            t["completed_ts"] = _now_iso()
            ok = True
            break
    if ok:
        write_data(d)
        audit("task_complete", nurse_id, f"task:{task_id}", {})
    else:
        raise ValueError("Task not found or not assigned to you.")

def list_notifications(nurse_id: str) -> List[Dict[str, Any]]:
    d = read_data()
    return [n for n in d.get("notifications", []) if n["nurse_id"] == nurse_id]

def ack_notification(notif_id: str, nurse_id: str) -> None:
    d = read_data()
    for n in d.get("notifications", []):
        if n["id"] == notif_id and n["nurse_id"] == nurse_id:
            n["ack"] = True
            n["ack_ts"] = _now_iso()
            write_data(d)
            audit("notif_ack", nurse_id, f"notif:{notif_id}", {})
            return
    raise ValueError("Notification not found.")

def send_message(nurse_id: str, to_role: str, patient_id: str, text: str, urgent: bool = False) -> Dict[str, Any]:
    d = read_data()
    msg = {
        "id": f"msg_{len(d.get('messages', [])) + 1}",
        "ts": _now_iso(),
        "from": f"nurse:{nurse_id}",
        "to": to_role,
        "patient_id": patient_id,
        "text": text,
        "urgent": urgent,
        "status": "sent",
    }
    d.setdefault("messages", []).append(msg)
    write_data(d)
    audit("message_send", nurse_id, f"patient:{patient_id}", {"to": to_role, "urgent": urgent})
    return msg
