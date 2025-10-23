# carelog_doctor/doctor_name_services/data_store.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List

# IMPORTANT: this module must NOT import anything from auth.py that would pull us back here.
# One-way dependency is OK: auth.py should not import data_store.py.
from doctor_name_services.auth import current_doctor  # one-way

# ---------- Paths ----------
DATA_DIR = (Path(__file__).resolve().parents[1] / "doctor_name_data")
UPLOAD_DIR = (Path(__file__).resolve().parents[1] / "uploads")
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "doctors": DATA_DIR / "doctors.json",
    "patients": DATA_DIR / "patients.json",
    "appointments": DATA_DIR / "appointments.json",
    "messages": DATA_DIR / "messages.json",
    "encounters": DATA_DIR / "encounters.json",
    "audit": DATA_DIR / "audit.log",
}

# ---------- JSON helpers (exported so other services can reuse) ----------
def _read_json(path: Path, default: Any):
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return default

def _write_json(path: Path, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------- DataStore ----------
class DataStore:
    """
    Lightweight JSON-backed store to satisfy the Doctor module requirements.
    Safe for a single-user demo. Not for production.
    """
    def __init__(self):
        self._bootstrap()

    # Seed minimal demo data so the UI can run immediately
    def _bootstrap(self):
        _read_json(
            FILES["doctors"],
            [{
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
            }],
        )
        _read_json(
            FILES["patients"],
            [
                {
                    "id": "p1",
                    "name": "Alex Rivers",
                    "contact": "+60-10-000-1111",
                    "assigned_doctor_ids": ["doc1"],
                    "consent_to_all_doctors": False,
                    "conditions": ["Hypertension"],
                    "allergies": ["Penicillin"],
                    "medications": ["Amlodipine"],
                    "history": ["Admitted 2023-04"],
                    "uploads": []
                },
                {
                    "id": "p2",
                    "name": "Nicole Tan",
                    "contact": "+60-10-000-2222",
                    "assigned_doctor_ids": [],
                    "consent_to_all_doctors": True,
                    "conditions": ["Post-op knee"],
                    "allergies": [],
                    "medications": ["Paracetamol"],
                    "history": ["Surgery 2024-12"],
                    "uploads": []
                },
            ],
        )
        _read_json(FILES["appointments"], [])
        _read_json(FILES["messages"], [])
        _read_json(FILES["encounters"], [])
        if not FILES["audit"].exists():
            FILES["audit"].write_text("", encoding="utf-8")

    # ---------- Doctor profile ----------
    def update_doctor_profile(self, **kwargs):
        docs = _read_json(FILES["doctors"], [])
        me = current_doctor()
        for d in docs:
            if d.get("id") == me.get("id"):
                d.update({k: v for k, v in kwargs.items() if v is not None})
                break
        _write_json(FILES["doctors"], docs)
        self.audit("profile.update", target=me.get("id", ""))

    # ---------- Metrics for dashboard ----------
    def count_assigned_patients(self) -> int:
        me = current_doctor()
        patients = _read_json(FILES["patients"], [])
        return sum(
            1 for p in patients
            if (me.get("id") in p.get("assigned_doctor_ids", [])) or p.get("consent_to_all_doctors", False)
        )

    def count_today_appts(self) -> int:
        appts = _read_json(FILES["appointments"], [])
        me = current_doctor()
        today = datetime.now().date()
        return sum(
            1
            for a in appts
            if a.get("doctor_id") == me.get("id") and str(a.get("start", ""))[:10] == today.isoformat()
        )

    def count_unread_messages(self) -> int:
        threads = _read_json(FILES["messages"], [])
        me = current_doctor()
        return sum(1 for t in threads if t.get("doctor_id") == me.get("id") and t.get("status") == "open")

    def count_recent_edits(self) -> int:
        encs = _read_json(FILES["encounters"], [])
        cutoff = datetime.now() - timedelta(days=7)
        count = 0
        for e in encs:
            for v in e.get("versions", []):
                try:
                    if datetime.fromisoformat(v.get("timestamp", "")) >= cutoff:
                        count += 1
                        break
                except Exception:
                    pass
        return count

    def list_upcoming_appointments(self, limit: int = 10) -> List[Dict[str, Any]]:
        appts = _read_json(FILES["appointments"], [])
        me = current_doctor()
        now_iso = datetime.now().isoformat()
        rows = [a for a in appts if a.get("doctor_id") == me.get("id") and a.get("start", "") >= now_iso]
        rows.sort(key=lambda x: x.get("start", ""))
        return rows[:limit]

    # ---------- Patients ----------
    def list_assigned_or_consented_patients(self) -> List[Dict[str, Any]]:
        me = current_doctor()
        patients = _read_json(FILES["patients"], [])
        rows = []
        for p in patients:
            if (me.get("id") in p.get("assigned_doctor_ids", [])) or p.get("consent_to_all_doctors", False):
                rows.append({"id": p["id"], "name": p["name"], "contact": p["contact"]})
        return rows

    # ---------- Uploads ----------
    def save_upload(self, patient_id: str, filename: str, content: bytes) -> str:
        safe_name = f"{patient_id}_{filename}"
        path = (UPLOAD_DIR / safe_name).as_posix()
        with open(path, "wb") as f:
            f.write(content)

        pats = _read_json(FILES["patients"], [])
        for p in pats:
            if p.get("id") == patient_id:
                p.setdefault("uploads", []).append(path)
                break
        _write_json(FILES["patients"], pats)
        self.audit("attachment.upload", target=patient_id, extra={"file": safe_name})
        return path

    # ---------- Audit ----------
    def audit(self, action: str, target: str = "", extra: dict | None = None):
        me = current_doctor()
        rec = {
            "timestamp": datetime.now().isoformat(),
            "user_id": me.get("id", "?"),
            "action": action,
            "target": target,
            "extra": extra or {},
        }
        with open(FILES["audit"], "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    
    def doctor_display_name(self) -> str:
        me_id = current_doctor().get("id")
        docs = _read_json(FILES["doctors"], [])
        for d in docs:
            if d.get("id") == me_id:
                return d.get("name") or d.get("email") or f"Doctor {me_id}"
        return "Doctor"

    def doctor_average_rating(self) -> tuple[float, int]:
        """Returns (avg_rating, num_ratings) for the current doctor based on patients.json 'ratings' list."""
        me_id = current_doctor().get("id")
        pts = _read_json(FILES["patients"], [])
        scores = []
        for p in pts:
            for r in p.get("ratings", []):
                if r.get("doctor_id") == me_id and isinstance(r.get("score"), (int, float)):
                    scores.append(float(r["score"]))
        if not scores:
            return (0.0, 0)
        avg = round(sum(scores) / len(scores), 1)
        return (avg, len(scores))

