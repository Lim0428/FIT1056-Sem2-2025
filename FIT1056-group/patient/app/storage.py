# app/storage.py
import os, json, threading
from typing import Any, Dict

_LOCK = threading.Lock()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _repo_root_data_dir() -> str:
    cur = BASE_DIR
    for _ in range(10):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        if os.path.isdir(os.path.join(parent, "patient")) and os.path.isdir(os.path.join(parent, "data")):
            return os.path.join(parent, "data")
        cur = parent
    raise RuntimeError("Repo data folder not found. Expect <REPO>/data and <REPO>/patient.")

_DATA_DIR = _repo_root_data_dir()

def data_dir() -> str:  # optional helper
    return _DATA_DIR

FILE_MAP = {
    "users":         "users.json",
    "patients":      "patient.json",   # ← singular file name holds the patients dict
    "surveys":       "surveys.json",
    "feedback":      "feedback.json",
    "messages":      "messages.json",
    "appointments":  "appointments.json",
    "doctors":       "doctors.json",
    "medical_staff": "medical_staff.json",
    "encounters":    "encounters.json",
}
SEQ_PATH = os.path.join(_DATA_DIR, "seq.json")

_DEFAULT = {
    "users": {},
    "patients": {},
    "surveys": {},
    "feedback": {},
    "messages": [],
    "appointments": [],
    "doctors": {},
    "medical_staff": {},
    "encounters": {},
    "seq": {"user": 1, "appt": 1},
}

def _read_json(path: str, default: Any):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _infer_seq_from_data(db: Dict[str, Any]) -> Dict[str, int]:
    next_user = 1
    for uid in (db.get("users") or {}):
        if isinstance(uid, str) and uid.startswith("P"):
            try: next_user = max(next_user, int(uid[1:]) + 1)
            except: pass
    next_appt = 1
    for a in (db.get("appointments") or []):
        sid = a.get("id")
        if isinstance(sid, str) and sid.startswith("A"):
            try: next_appt = max(next_appt, int(sid[1:]) + 1)
            except: pass
    return {"user": next_user, "appt": next_appt}

def read_db() -> Dict[str, Any]:
    with _LOCK:
        db: Dict[str, Any] = {k: _DEFAULT[k] for k in _DEFAULT}
        for key, fname in FILE_MAP.items():
            db[key] = _read_json(os.path.join(_DATA_DIR, fname), _DEFAULT[key])
        seq = _read_json(SEQ_PATH, None)
        if not isinstance(seq, dict) or not seq:
            seq = _infer_seq_from_data(db) or {"user": 1, "appt": 1}
            _write_json(SEQ_PATH, seq)
        else:
            try: seq["user"] = max(1, int(seq.get("user", 1)))
            except: seq["user"] = 1
            try: seq["appt"] = max(1, int(seq.get("appt", 1)))
            except: seq["appt"] = 1
        db["seq"] = seq
        return db

def write_db(db: Dict[str, Any]) -> None:
    if not isinstance(db, dict): return
    with _LOCK:
        for key, fname in FILE_MAP.items():
            _write_json(os.path.join(_DATA_DIR, fname), db.get(key, _DEFAULT[key]))
        seq = db.get("seq", _DEFAULT["seq"])
        try: u = max(1, int(seq.get("user", 1)))
        except: u = 1
        try: a = max(1, int(seq.get("appt", 1)))
        except: a = 1
        _write_json(SEQ_PATH, {"user": u, "appt": a})
