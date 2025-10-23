import os, json, threading
from typing import Any, Dict

# Resolve project-relative data path (works on Windows/macOS/Linux)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # .../services
ROOT_DIR = os.path.dirname(BASE_DIR)                    # project root
DATA_DIR = os.path.join(ROOT_DIR, "data")
DATA_PATH = os.path.join(DATA_DIR, "carelog.json")
_LOCK = threading.Lock()

_DEFAULT = {
    "users": {},             # id -> user
    "patients": {},          # id -> patient profile
    "surveys": {},           # patient_id -> [ ... ]
    "feedback": {},          # patient_id -> [ ... ]
    "messages": [],          # [{from_patient,to_role,content,ts}]
    "appointments": [],      # [{id,patient_id,dt,note}]
    "seq": {"user": 1, "appt": 1}
}

def _ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(_DEFAULT, f, indent=2)

def read_db() -> Dict[str, Any]:
    _ensure_file()
    with _LOCK:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return _DEFAULT.copy()

def write_db(db: Dict[str, Any]) -> None:
    with _LOCK:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
