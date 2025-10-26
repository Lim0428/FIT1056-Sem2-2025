# admin_name_utils/appointments_io.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
import json

# -------- paths --------
def _project_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / "data").is_dir():
            return p
    return Path.cwd()

def _data_dir() -> Path:
    return _project_root() / "data"

def appointments_file_path() -> Path:
    return _data_dir() / "appointments.json"

# -------- I/O --------
def load_appointments() -> List[Dict[str, Any]]:
    """
    Read data/appointments.json.
    Normalizes keys to the app's shape:
      - start_iso / end_iso (accepts 'start'/'end' as fallback)
      - status defaults to 'booked'
      - keeps patient_id, doctor_id, nurse_id, id, notes, etc. if present
    """
    p = appointments_file_path()
    if not p.exists():
        return []

    try:
        data = json.loads(p.read_text(encoding="utf-8")) or []
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    out: List[Dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        start_iso = row.get("start_iso") or row.get("start") or ""
        end_iso   = row.get("end_iso") or row.get("end") or ""
        status    = (row.get("status") or "booked").lower()

        # carry through common fields; ignore unknowns safely
        out.append({
            "id": row.get("id"),
            "patient_id": row.get("patient_id"),
            "doctor_id": row.get("doctor_id"),
            "nurse_id": row.get("nurse_id"),
            "room_id": row.get("room_id"),
            "start_iso": str(start_iso),
            "end_iso": str(end_iso) if end_iso else "",
            "status": status,
            "notes": row.get("notes", ""),
        })
    return out

def save_appointments(appts: List[Dict[str, Any]]) -> None:
    """
    Optional: write back to data/appointments.json (keeps a simple array shape).
    """
    p = appointments_file_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    # Keep as-is (no extra transformations)
    p.write_text(json.dumps(appts, ensure_ascii=False, indent=2), encoding="utf-8")
