# admin_name_utils/storage.py
from __future__ import annotations

import json, os
from pathlib import Path
from typing import Any, Dict, List, Optional
from tempfile import NamedTemporaryFile

# ---------------- project paths ----------------
def _project_root() -> Path:
    """Resolve the repo root that contains the /data folder."""
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / "data").is_dir():
            return p
    return Path.cwd()

def _data_dir() -> Path:
    return _project_root() / "data"

def _db_path() -> Path:
    # internal app DB (small, for non-patient things)
    return _data_dir() / "carelog.json"

# ========== atomic write ==========
def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)

# ========== small app DB ==========
def _ensure_db_file() -> None:
    p = _db_path()
    if not p.exists():
        p.write_text(json.dumps({
            "users": [],
            "patients": [],        # mirror list (derived from patient.json)
            "appointments": [],
            "rooms": [],
            "messages": [],
            "invoices": [],
            "ratings": [],
            "login_attempts": {}
        }, ensure_ascii=False, indent=2), encoding="utf-8")

def load_db() -> Dict[str, Any]:
    _ensure_db_file()
    try:
        raw = json.loads(_db_path().read_text(encoding="utf-8")) or {}
    except Exception:
        raw = {}
    raw.setdefault("users", [])
    raw.setdefault("patients", [])
    raw.setdefault("appointments", [])
    raw.setdefault("rooms", [])
    raw.setdefault("messages", [])
    raw.setdefault("invoices", [])
    raw.setdefault("ratings", [])
    raw.setdefault("login_attempts", {})
    return raw

def save_db(db: Dict[str, Any]) -> None:
    _ensure_db_file()
    _atomic_write(_db_path(), json.dumps(db, ensure_ascii=False, indent=2))

def bootstrap_store() -> None:
    _data_dir().mkdir(parents=True, exist_ok=True)
    _ensure_db_file()

def next_id(arr: List[Dict[str, Any]], key: str = "id") -> int:
    try:
        return max([int(x.get(key, 0)) for x in arr] + [0]) + 1
    except Exception:
        return 1

# ========== Patients: STRICTLY data/patient.json (singular) ==========
PAT_FIELDS = [
    "id","name","dob","gender","mrn","medical_details","emergency_contact",
    "avatar_path","pref_food","pref_language","pref_nurse_gender","visible_to_non_primary"
]

def patients_file_path() -> Path:
    """Always use data/patient.json (singular)."""
    return _data_dir() / "patient.json"

def _blank_patient_payload() -> Dict[str, Dict[str, Any]]:
    return {}

def load_patients_file() -> Dict[str, Dict[str, Any]]:
    """
    Load STRICT patient file keyed by codes like P000001 -> {...exact fields...}.
    Returns {} if file missing or invalid.
    """
    p = patients_file_path()
    if not p.exists():
        return _blank_patient_payload()
    try:
        raw = json.loads(p.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            return _blank_patient_payload()
    except Exception:
        return _blank_patient_payload()

    out: Dict[str, Dict[str, Any]] = {}
    for key, val in raw.items():
        if not isinstance(val, dict):
            continue
        rec = {f: val.get(f, "") for f in PAT_FIELDS}
        rec["visible_to_non_primary"] = bool(val.get("visible_to_non_primary", False))
        rec["id"] = rec["id"] or key
        out[key] = rec
    return out

def save_patients_file(obj: Dict[str, Dict[str, Any]]) -> None:
    """
    Write EXACT structure back to data/patient.json.
    """
    path = patients_file_path()
    payload: Dict[str, Dict[str, Any]] = {}
    for key, v in obj.items():
        rec = {f: v.get(f, "") for f in PAT_FIELDS}
        rec["visible_to_non_primary"] = bool(v.get("visible_to_non_primary", False))
        rec["id"] = rec["id"] or key
        payload[key] = rec
    _atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2))

def patients_file_to_app_list(obj: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert strict dict to the app’s list shape (numeric id + code)."""
    out: List[Dict[str, Any]] = []
    for key, v in obj.items():
        try:
            num_id = int(str(key)[1:])
        except Exception:
            num_id = 0
        rec = {"id": num_id, "code": key}
        for f in PAT_FIELDS:
            if f == "id":
                continue
            rec[f] = v.get(f, "")
        out.append(rec)
    out.sort(key=lambda r: r.get("id", 0))
    return out

# ========== Admin credentials in data/admins.json ==========
def admins_file_path() -> Path:
    return _data_dir() / "admins.json"

def load_admins() -> List[Dict[str, Any]]:
    p = admins_file_path()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8")) or []
        if isinstance(data, list):
            out = []
            for u in data:
                if not isinstance(u, dict):
                    continue
                out.append({
                    "id": int(u.get("id", 1)),
                    "name": u.get("name", "Admin"),
                    "email": u.get("email", "admin@carelog.local"),
                    "role": "admin",
                    "locked": bool(u.get("locked", False)),
                    "pwd": u.get("pwd", "admin123"),
                })
            return out
        return []
    except Exception:
        return []

def save_admins(admins: List[Dict[str, Any]]) -> None:
    cleaned = []
    for u in admins:
        cleaned.append({
            "id": int(u.get("id", 1)),
            "name": u.get("name", "Admin"),
            "email": u.get("email", "admin@carelog.local"),
            "role": "admin",
            "locked": bool(u.get("locked", False)),
            "pwd": u.get("pwd", "admin123"),
        })
    _atomic_write(admins_file_path(), json.dumps(cleaned, ensure_ascii=False, indent=2))

# ========== External app users in data/admin_users.json ==========
def admin_users_file_path() -> Path:
    return _data_dir() / "admin_users.json"

def load_admin_users() -> List[Dict[str, Any]]:
    p = admin_users_file_path()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8")) or []
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for u in data if isinstance(data, list) else []:
        if not isinstance(u, dict):
            continue
        uid = u.get("id", 0)
        try:
            uid = int(uid)
        except Exception:
            pass
        out.append({
            "id": uid,
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "role": (u.get("role", "staff") or "staff").lower(),
            "locked": bool(u.get("locked", False)),
            "pwd": u.get("pwd", "changeme123"),
            "specialization": u.get("specialization", u.get("specialty", "")),
            "qualifications": u.get("qualifications", ""),
            "availability": u.get("availability", []),
            "note": u.get("note", ""),
            "code": u.get("code", ""),
        })
    return out

def save_admin_users(users: List[Dict[str, Any]]) -> None:
    p = admin_users_file_path()
    payload = []
    for u in users:
        payload.append({
            "id": u.get("id"),
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "role": (u.get("role", "staff") or "staff").lower(),
            "locked": bool(u.get("locked", False)),
            "pwd": u.get("pwd", "changeme123"),
            "specialization": u.get("specialization", ""),
            "qualifications": u.get("qualifications", ""),
            "availability": u.get("availability", []),
            "note": u.get("note", ""),
            "code": u.get("code", ""),
        })
    _atomic_write(p, json.dumps(payload, ensure_ascii=False, indent=2))

# Back-compat alias (some pages import this)
def external_admin_users() -> List[Dict[str, Any]]:
    return load_admin_users()
