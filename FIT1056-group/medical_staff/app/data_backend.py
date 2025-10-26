# medical_staff/app/data_backend.py
from __future__ import annotations
import os, json, threading
from typing import Any, Dict
from datetime import datetime

_LOCK = threading.RLock()

def _find_project_data_dir() -> str:
    """
    Locate the project's real /data folder.

    Order of precedence:
      1) FIT1056_DATA_DIR env var, if set and valid
      2) Walk upwards from this file to find a parent with 'data/patient.json'
      3) Fallback: two-levels-up '/data' (FIT1056-group/data)
    """
    # 1) Env override
    env_dir = os.environ.get("FIT1056_DATA_DIR")
    if env_dir:
        pd = os.path.join(env_dir)
        if os.path.isdir(pd):
            return os.path.normpath(pd)

    # 2) Walk up to find a 'data' containing patient.json OR existing dir
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(8):  # don't walk forever
        candidate = os.path.normpath(os.path.join(cur, "data"))
        if os.path.isdir(candidate):
            # Prefer if patient.json exists here (your case)
            pj = os.path.join(candidate, "patient.json")
            if os.path.exists(pj):
                return candidate
            # If no patient.json yet but data dir exists, still accept
            return candidate
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    # 3) Fallback to ../../data relative to this file (your repo layout)
    return os.path.normpath(os.path.join(here, "..", "..", "data"))

DATA_DIR = _find_project_data_dir()

# ALWAYS use patient.json (as requested)
PATHS = {
    "patients":      os.path.join(DATA_DIR, "patient.json"),
    "appointments":  os.path.join(DATA_DIR, "appointments.json"),
    "messages":      os.path.join(DATA_DIR, "messages.json"),
    "staff":         os.path.join(DATA_DIR, "medical_staff.json"),
    "encounters":    os.path.join(DATA_DIR, "encounters.json"),
    "tasks":         os.path.join(DATA_DIR, "tasks.json"),
    "handover":      os.path.join(DATA_DIR, "handover.json"),
    "documents":     os.path.join(DATA_DIR, "documents.json"),
    "audit_log":     os.path.join(DATA_DIR, "audit.log"),  # JSON Lines
    "seq":           os.path.join(DATA_DIR, "seq.json"),
    "uploads_dir":   os.path.join(DATA_DIR, "uploads"),
}

def _ensure_dirs() -> None:
    # Only ensure the real /data and /data/uploads in the project root
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PATHS["uploads_dir"], exist_ok=True)

def _read_json(path: str, default: Any) -> Any:
    _ensure_dirs()
    # Create the file with default if missing/empty
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return json.loads(json.dumps(default))
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Reset corrupt file to default
            with open(path, "w", encoding="utf-8") as wf:
                json.dump(default, wf, indent=2)
            return json.loads(json.dumps(default))

def _write_json(path: str, data: Any) -> None:
    _ensure_dirs()
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    _ensure_dirs()
    line = json.dumps(obj, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ---------- public helpers ----------
def jread(name: str, default: Any):
    with _LOCK:
        return _read_json(PATHS[name], default)

def jwrite(name: str, data: Any) -> None:
    with _LOCK:
        _write_json(PATHS[name], data)

def jappend_audit(who: str, action: str, target: str, detail: str = "") -> None:
    with _LOCK:
        _append_jsonl(PATHS["audit_log"], {
            "when": datetime.now().isoformat(timespec="seconds"),
            "who": who, "action": action, "target": target, "detail": detail
        })

def read_seq() -> Dict[str, int]:
    with _LOCK:
        seq = _read_json(PATHS["seq"], {})
        changed = False
        for key in ("appt", "task", "doc", "enc", "staff", "msg"):
            if not isinstance(seq.get(key), int) or seq[key] < 1:
                seq[key] = 1
                changed = True
        if changed:
            _write_json(PATHS["seq"], seq)
        return seq

def bump_seq(key: str) -> int:
    with _LOCK:
        seq = read_seq()
        cur = int(seq.get(key, 1))
        seq[key] = cur + 1
        _write_json(PATHS["seq"], seq)
        return cur
