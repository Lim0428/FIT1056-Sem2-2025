# carelog_doctor/doctor_name_services/data_store.py
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Iterable

# One-way dependency OK: auth can import us, but we don't import from modules
# that would import us back (no circular imports).
from doctor_name_services.auth import current_doctor  # runtime provider of the logged-in doctor

# ---------- Paths ----------
DATA_DIR = (Path(__file__).resolve().parents[1] / "doctor_name_data")
UPLOAD_DIR = (Path(__file__).resolve().parents[1] / "uploads")
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

FILES: Dict[str, Path] = {
    "doctors": DATA_DIR / "doctors.json",
    "patients": DATA_DIR / "patients.json",
    "appointments": DATA_DIR / "appointments.json",
    "messages": DATA_DIR / "messages.json",
    "encounters": DATA_DIR / "encounters.json",
    "audit": DATA_DIR / "audit.log",
}

# ---------- JSON helpers ----------
def _read_json(path: Path, default: Any) -> Any:
    """
    Read JSON or create with default. Returns default on error.
    """
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------- Normalizers (robust against bad data) ----------
def _ensure_list_dicts(value: Any, wrapper_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Accepts:
      - list of dicts
      - {wrapper_key: [ ... ]} if wrapper_key provided
      - anything else -> []
    Filters out non-dict items.
    """
    items: Iterable[Any] = []
    if isinstance(value, dict) and wrapper_key and isinstance(value.get(wrapper_key), list):
        items = value[wrapper_key]
    elif isinstance(value, list):
        items = value
    else:
        items = []

    return [x for x in items if isinstance(x, dict)]


def _normalize_appointments(raw: Any) -> List[Dict[str, Any]]:
    return _ensure_list_dicts(raw, "appointments")


def _normalize_messages(raw: Any) -> List[Dict[str, Any]]:
    # messages are usually a list of thread dicts
    return _ensure_list_dicts(raw, None)


def _normalize_patients(raw: Any) -> List[Dict[str, Any]]:
    return _ensure_list_dicts(raw, "patients")


def _normalize_doctors(raw: Any) -> List[Dict[str, Any]]:
    return _ensure_list_dicts(raw, "doctors")


def _normalize_encounters(raw: Any) -> List[Dict[str, Any]]:
    return _ensure_list_dicts(raw, "encounters")

# ---------- DataStore ----------
class DataStore:
    """
    Lightweight JSON-backed store. Safe for single-user demo.
    """

    def __init__(self, files: Dict[str, Path] | None = None) -> None:
        self.files = files or FILES
        self._bootstrap_minimum()
        self.reload_all()

    # ----- Bootstrap with minimal files so the UI can run -----
    def _bootstrap_minimum(self) -> None:
        _read_json(self.files["doctors"], [{
            "id": "doc1",
            "email": "doc@example.com",
            "password": "pass123",
            "safety_q": "pet?",
            "safety_a": "milo",
            "specialty": "General Medicine",
            "qualifications": "MBBS",
            "license_no": "D-001",
            "working_hours": "Mon-Fri 9:00-17:00",
            "contact": "+60-12-345-6789"
        }])
        _read_json(self.files["patients"], [])
        _read_json(self.files["appointments"], [])
        _read_json(self.files["messages"], [])
        _read_json(self.files["encounters"], [])
        if not self.files["audit"].exists():
            self.files["audit"].write_text("", encoding="utf-8")

    # ----- Reloaders -----
    def reload_all(self) -> None:
        self._doctors    = _normalize_doctors(_read_json(self.files["doctors"], []))
        self._patients   = _normalize_patients(_read_json(self.files["patients"], []))
        self._appointments = _normalize_appointments(_read_json(self.files["appointments"], []))
        self._messages   = _normalize_messages(_read_json(self.files["messages"], []))
        self._encounters = _normalize_encounters(_read_json(self.files["encounters"], []))

    def reload_appointments(self) -> None:
        self._appointments = _normalize_appointments(_read_json(self.files["appointments"], []))

    # ----- Audit -----
    def audit(self, action: str, target: str = "", extra: dict | None = None) -> None:
        me = current_doctor() or {}
        rec = {
            "timestamp": datetime.now().isoformat(),
            "user_id": me.get("id", "?"),
            "action": action,
            "target": target,
            "extra": extra or {},
        }
        with open(self.files["audit"], "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    # ----- Doctor profile & metrics -----
    def doctor_display_name(self) -> str:
        me = current_doctor() or {}
        me_id = me.get("id")
        for d in self._doctors:
            if d.get("id") == me_id:
                return d.get("name") or d.get("email") or f"Doctor {me_id}"
        return "Doctor"

    def doctor_average_rating(self) -> tuple[float, int]:
        """Returns (avg_rating, num_ratings) based on patients[].ratings[]."""
        me = current_doctor() or {}
        me_id = me.get("id")
        scores: List[float] = []
        for p in self._patients:
            for r in p.get("ratings", []) or []:
                if r.get("doctor_id") == me_id and isinstance(r.get("score"), (int, float)):
                    scores.append(float(r["score"]))
        if not scores:
            return 0.0, 0
        avg = round(sum(scores) / len(scores), 1)
        return avg, len(scores)

    def update_doctor_profile(self, **kwargs) -> None:
        me = current_doctor() or {}
        me_id = me.get("id")
        docs = list(self._doctors)
        for d in docs:
            if d.get("id") == me_id:
                d.update({k: v for k, v in kwargs.items() if v is not None})
                break
        _write_json(self.files["doctors"], docs)
        self._doctors = docs
        self.audit("profile.update", target=me_id)

    # ----- Dashboard counters -----
    def count_assigned_patients(self) -> int:
        me = current_doctor() or {}
        me_id = me.get("id")
        count = 0
        for p in self._patients:
            if (me_id in p.get("assigned_doctor_ids", [])) or p.get("consent_to_all_doctors", False):
                count += 1
        return count

    def count_today_appts(self) -> int:
        me = current_doctor() or {}
        me_id = me.get("id")
        today = date.today().isoformat()
        n = 0
        for a in self._appointments:
            if not isinstance(a, dict):
                continue
            if me_id and a.get("doctor_id") != me_id:
                continue
            start = a.get("start")
            if start and str(start)[:10] == today:
                n += 1
        return n

    def count_unread_messages(self) -> int:
        me = current_doctor() or {}
        me_id = me.get("id")
        return sum(
            1
            for t in self._messages
            if isinstance(t, dict) and t.get("doctor_id") == me_id and t.get("status") == "open"
        )

    def count_recent_edits(self) -> int:
        cutoff = datetime.now() - timedelta(days=7)
        count = 0
        for e in self._encounters:
            for v in e.get("versions", []) or []:
                try:
                    if datetime.fromisoformat(str(v.get("timestamp", ""))) >= cutoff:
                        count += 1
                        break
                except Exception:
                    pass
        return count

    # ----- Appointments APIs -----
    def list_all_appointments(self) -> List[Dict[str, Any]]:
        """All appointments for the logged-in doctor (unsorted)."""
        me = current_doctor() or {}
        me_id = me.get("id")
        rows = [a for a in self._appointments if isinstance(a, dict)]
        if me_id:
            rows = [a for a in rows if a.get("doctor_id") == me_id]
        return rows

    def list_upcoming_appointments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Next appointments sorted by start time."""
        me = current_doctor() or {}
        me_id = me.get("id")

        def _key(a: Dict[str, Any]):
            try:
                return datetime.fromisoformat(str(a.get("start", "")).replace("Z", ""))
            except Exception:
                return datetime.max

        rows = [a for a in self._appointments if isinstance(a, dict)]
        if me_id:
            rows = [a for a in rows if a.get("doctor_id") == me_id]
        rows.sort(key=_key)
        return rows[:limit]

    def get_appointment(self, appt_id: str) -> Optional[Dict[str, Any]]:
        for a in self._appointments:
            if isinstance(a, dict) and a.get("id") == appt_id:
                return a
        return None

    # ----- Patients (subset) -----
    def list_assigned_or_consented_patients(self) -> List[Dict[str, Any]]:
        me = current_doctor() or {}
        me_id = me.get("id")
        rows: List[Dict[str, Any]] = []
        for p in self._patients:
            if (me_id in p.get("assigned_doctor_ids", [])) or p.get("consent_to_all_doctors", False):
                rows.append({"id": p.get("id"), "name": p.get("name"), "contact": p.get("contact")})
        return rows

    # ----- Uploads -----
    def save_upload(self, patient_id: str, filename: str, content: bytes) -> str:
        safe_name = f"{patient_id}_{filename}"
        path = (UPLOAD_DIR / safe_name).as_posix()
        with open(path, "wb") as f:
            f.write(content)

        pats = list(self._patients)
        for p in pats:
            if p.get("id") == patient_id:
                p.setdefault("uploads", []).append(path)
                break
        _write_json(self.files["patients"], pats)
        self._patients = pats
        self.audit("attachment.upload", target=patient_id, extra={"file": safe_name})
        return path
