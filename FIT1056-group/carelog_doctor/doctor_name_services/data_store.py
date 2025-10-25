# carelog_doctor/doctor_name_services/data_store.py
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional

# ---------- Paths: shared /data across all roles ----------
# repo_root / FIT1056-group
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "doctors":      DATA_DIR / "doctors.json",
    "patients":     DATA_DIR / "patients.json",
    "appointments": DATA_DIR / "appointments.json",
    "messages":     DATA_DIR / "messages.json",
    "encounters":   DATA_DIR / "encounters.json",
    "audit":        DATA_DIR / "audit.log",
}

# ---------- tiny JSON helpers ----------
def _read_json(path: Path, default: Any):
    if not path.exists():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, ensure_ascii=False, indent=2)
        except Exception:
            return default
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- normalizers ----------
def _normalize_appointments(raw: Any) -> List[Dict[str, Any]]:
    """
    Accept either:
      • list[dict]
      • {"appointments": [ ... ]}
    Return: list of dicts
    """
    items: Any
    if isinstance(raw, dict) and isinstance(raw.get("appointments"), list):
        items = raw["appointments"]
    elif isinstance(raw, list):
        items = raw
    else:
        items = []
    return [a for a in items if isinstance(a, dict)]

def _parse_iso(iso: Any) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(iso).replace("Z", ""))
    except Exception:
        return None

# ---------- bootstrap shared data ----------
def ensure_bootstrap_data() -> None:
    """Create minimal shared JSON files if missing (in ../data)."""
    _read_json(
        FILES["doctors"],
        [{
            "id": "doc1",
            "email": "doc@example.com",
            "password": "pass123",
            "name": "Dr. Example",
            "specialty": "General Medicine",
            "qualifications": "MBBS",
            "license_no": "D-001",
            "working_hours": "Mon–Fri 9:00–17:00",
            "contact": "+60-12-345-6789",
            "safety_q": "pet?", "safety_a": "milo",
            "avatar": None
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
                "treatments": [],
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
                "treatments": [],
                "uploads": []
            },
        ],
    )
    _read_json(FILES["appointments"], [])
    _read_json(FILES["messages"], [])
    _read_json(FILES["encounters"], [])
    if not FILES["audit"].exists():
        FILES["audit"].write_text("", encoding="utf-8")

# ---------- DataStore ----------
class DataStore:
    """
    Shared JSON-backed store.
    Provides helpers used throughout the Doctor app pages.
    """

    # ----- Doctor / auth glue -----
    @staticmethod
    def _current_doctor() -> Optional[Dict[str, Any]]:
        """Lazy import to avoid circular import issues."""
        try:
            from doctor_name_services.auth import current_doctor  # type: ignore
            return current_doctor()
        except Exception:
            return None

    # ----- Dashboard metrics -----
    def count_assigned_patients(self) -> int:
        me = self._current_doctor() or {}
        me_id = me.get("id")
        patients = _read_json(FILES["patients"], [])
        return sum(
            1 for p in patients if isinstance(p, dict) and (
                (me_id and me_id in p.get("assigned_doctor_ids", [])) or
                p.get("consent_to_all_doctors", False)
            )
        )

    def count_today_appts(self) -> int:
        """Count appointments today for the logged-in doctor."""
        me = self._current_doctor() or {}
        me_id = me.get("id")
        appts = _normalize_appointments(_read_json(FILES["appointments"], []))
        today_str = date.today().isoformat()
        count = 0
        for a in appts:
            if me_id and a.get("doctor_id") != me_id:
                continue
            start = a.get("start")
            if start and str(start)[:10] == today_str:
                count += 1
        return count

    def count_unread_messages(self) -> int:
        """Open threads for me (simple heuristic)."""
        me = self._current_doctor() or {}
        me_id = me.get("id")
        threads = _read_json(FILES["messages"], [])
        c = 0
        for t in threads:
            if not isinstance(t, dict):
                continue
            # If your schema tracks doctor_id on thread:
            if me_id and t.get("doctor_id") not in (None, me_id):
                continue
            if t.get("status", "open") == "open":
                c += 1
        return c

    def count_recent_edits(self) -> int:
        """Encounter versions edited in the last 7 days."""
        encs = _read_json(FILES["encounters"], [])
        cutoff = datetime.now() - timedelta(days=7)
        cnt = 0
        for e in encs:
            for v in e.get("versions", []):
                dt = _parse_iso(v.get("timestamp", ""))
                if dt and dt >= cutoff:
                    cnt += 1
                    break
        return cnt

    # ----- Appointments -----
    def list_all_appointments(self) -> List[Dict[str, Any]]:
        return _normalize_appointments(_read_json(FILES["appointments"], []))

    def list_upcoming_appointments(self, limit: int = 10) -> List[Dict[str, Any]]:
        me = self._current_doctor() or {}
        me_id = me.get("id")
        now = datetime.now()
        appts = [
            a for a in self.list_all_appointments()
            if (not me_id or a.get("doctor_id") == me_id)
        ]
        appts = [a for a in appts if (_parse_iso(a.get("start")) or datetime.min) >= now]
        appts.sort(key=lambda x: _parse_iso(x.get("start")) or datetime.max)
        return appts[:limit]

    # ----- Patients -----
    def list_assigned_or_consented_patients(self) -> List[Dict[str, Any]]:
        me = self._current_doctor() or {}
        me_id = me.get("id")
        pts = _read_json(FILES["patients"], [])
        rows: List[Dict[str, Any]] = []
        for p in pts:
            if not isinstance(p, dict):
                continue
            if (me_id and me_id in p.get("assigned_doctor_ids", [])) or p.get("consent_to_all_doctors", False):
                rows.append({"id": p.get("id"), "name": p.get("name"), "contact": p.get("contact")})
        return rows

    # ----- Doctor profile helpers -----
    def update_doctor_profile(self, **kwargs):
        docs = _read_json(FILES["doctors"], [])
        me = self._current_doctor() or {}
        me_id = me.get("id")
        for d in docs:
            if isinstance(d, dict) and d.get("id") == me_id:
                d.update({k: v for k, v in kwargs.items() if v is not None})
                break
        _write_json(FILES["doctors"], docs)
        self.audit("profile.update", target=(me_id or ""))

    def doctor_display_name(self) -> str:
        me = self._current_doctor() or {}
        me_id = me.get("id")
        docs = _read_json(FILES["doctors"], [])
        for d in docs:
            if d.get("id") == me_id:
                return d.get("name") or d.get("email") or f"Doctor {me_id}"
        return "Doctor"

    def doctor_average_rating(self) -> tuple[float, int]:
        """Returns (avg_rating, num_ratings) for the current doctor based on patients.json 'ratings' list."""
        me = self._current_doctor() or {}
        me_id = me.get("id")
        pts = _read_json(FILES["patients"], [])
        scores: List[float] = []
        for p in pts:
            for r in p.get("ratings", []):
                if r.get("doctor_id") == me_id and isinstance(r.get("score"), (int, float)):
                    scores.append(float(r["score"]))
        if not scores:
            return (0.0, 0)
        avg = round(sum(scores) / len(scores), 1)
        return (avg, len(scores))

    # ----- Uploads -----
    def save_upload(self, patient_id: str, filename: str, content: bytes) -> str:
        safe_name = f"{patient_id}_{filename}"
        out_path = (UPLOAD_DIR / safe_name)
        with open(out_path, "wb") as f:
            f.write(content)

        pats = _read_json(FILES["patients"], [])
        for p in pats:
            if p.get("id") == patient_id:
                p.setdefault("uploads", []).append(out_path.as_posix())
                break
        _write_json(FILES["patients"], pats)
        self.audit("attachment.upload", target=patient_id, extra={"file": safe_name})
        return out_path.as_posix()

    # ----- Audit -----
    def audit(self, action: str, target: str = "", extra: Optional[dict] = None):
        me = self._current_doctor() or {}
        rec = {
            "timestamp": datetime.now().isoformat(),
            "user_id": me.get("id", "?"),
            "action": action,
            "target": target,
            "extra": extra or {},
        }
        with open(FILES["audit"], "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
