# medical_staff/app/staff_db.py
from __future__ import annotations
import os, json, threading
from typing import Any, Dict, List

_LOCK = threading.Lock()

# Resolve .../medical_staff/app -> .../data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "data"))
STAFF_PATH = os.path.join(DATA_DIR, "medical_staff.json")
SEQ_PATH   = os.path.join(DATA_DIR, "seq.json")

def _ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

def _read_json(path: str, default: Any) -> Any:
    _ensure_dirs()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        # create with default
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return json.loads(json.dumps(default))  # deep copy
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # file corrupted → reset to default
            return json.loads(json.dumps(default))

def _write_json(path: str, data: Any) -> None:
    _ensure_dirs()
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

# --------- public, low-level helpers ---------
def read_staff_items() -> List[Dict[str, Any]]:
    """Return staff items as a LIST of dicts. Accepts {} legacy structure too."""
    with _LOCK:
        raw = _read_json(STAFF_PATH, default=[])
        if isinstance(raw, dict):
            # legacy: {"S001": {...}, "S002": {...}}
            out: List[Dict[str, Any]] = []
            for k, v in raw.items():
                row = dict(v or {})
                row.setdefault("id", k)
                out.append(row)
            return out
        return list(raw)

def write_staff_items(items: List[Dict[str, Any]]) -> None:
    """Persist staff items as a list (canonical format)."""
    with _LOCK:
        _write_json(STAFF_PATH, list(items))

def read_seq() -> Dict[str, Any]:
    with _LOCK:
        seq = _read_json(SEQ_PATH, default={})
        if "staff" not in seq or not isinstance(seq["staff"], int) or seq["staff"] < 1:
            seq["staff"] = 1
            _write_json(SEQ_PATH, seq)
        return seq

def bump_staff_seq() -> int:
    with _LOCK:
        seq = read_seq()
        cur = int(seq.get("staff", 1))
        seq["staff"] = cur + 1
        _write_json(SEQ_PATH, seq)
        return cur
