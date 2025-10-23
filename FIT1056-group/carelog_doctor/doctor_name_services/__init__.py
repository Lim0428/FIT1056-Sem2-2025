import json, os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from doctor_name_services.auth import current_doctor
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "doctor_name_data"
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "doctors": DATA_DIR / "doctors.json",
    "patients": DATA_DIR / "patients.json",
    "appointments": DATA_DIR / "appointments.json",
    "messages": DATA_DIR / "messages.json",
    "encounters": DATA_DIR / "encounters.json",
    "audit": DATA_DIR / "audit.log"
}

def _read_json(path, default):
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return default

def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

class DataStore:
    def __init__(self):
        # bootstrap minimal sample data
        self._bootstrap()

    def _bootstrap(self):
        _read_json(FILES["doctors"], [{"id":"doc1","email":"doc@example.com","password":"pass123","safety_q":"pet?","safety_a":"milo","specialty":"General Medicine","qualifications":"MBBS","license_no":"D-001","working_hours":"Mon-Fri 9:00-17:00","contact":"+60-12-345-6789"}])
        _read_json(FILES["patients"], [
            {"id":"p1","name":"Alex Rivers","contact":"+60-10-000-1111","assigned_doctor_ids":["doc1"],"consent_to_all_doctors":False,
             "conditions":["Hypertension"],"allergies":["Penicillin"],"medications":["Amlodipine"],"history":["Admitted 2023-04"], "uploads":[]},
            {"id":"p2","name":"Nicole Tan","contact":"+60-10-000-2222","assigned_doctor_ids":[],"consent_to_all_doctors":True,
             "conditions":["Post-op knee"],"allergies":[],"medications":["Paracetamol"],"history":["Surgery 2024-12"], "uploads":[]}
        ])
        _read_json(FILES["appointments"], [])
        _read_json(FILES["messages"], [])
        _read_json(FILES["encounters"], [])
        if not FILES["audit"].exists():
            FILES["audit"].write_text("", encoding="utf-8")

    # --- Doctor profile ---
    def update_doctor_profile(self, **kwargs):
        docs = _read_json(FILES["doctors"], [])
        me = current_doctor()
        for d in docs:
            if d["id"] == me["id"]:
                d.update({k:v for k,v in kwargs.items() if v is not None})
        _write_json(FILES["doctors"], docs)
        self.audit("profile.update", target=me["id"])

    # --- Metrics ---
    def count_assigned_patients(self) -> int:
        me = current_doctor()
        patients = _read_json(FILES["patients"], [])
        c = 0
        for p in patients:
            if (me["id"] in p.get("assigned_doctor_ids", [])) or p.get("consent_to_all_doctors"):
                c += 1
        return c

    def count_today_appts(self) -> int:
        from datetime import datetime
        me = current_doctor()
        appts = _read_json(FILES["appointments"], [])
        today = datetime.now().date()
        return sum(1 for a in appts if a["doctor_id"]==me["id"] and a["start"][:10]==today.isoformat())

    def count_unread_messages(self) -> int:
        msgs = _read_json(FILES["messages"], [])
        me = current_doctor()
        c = 0
        for t in msgs:
            if t["doctor_id"]==me["id"] and t["status"]=="open":
                # if any patient message not seen?
                c += 1
        return c

    def count_recent_edits(self) -> int:
        enc = _read_json(FILES["encounters"], [])
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=7)
        c = 0
        for e in enc:
            for v in e.get("versions",[]):
                try:
                    if datetime.fromisoformat(v.get("timestamp","")) >= cutoff:
                        c += 1
                        break
                except:
                    pass
        return c

    def list_upcoming_appointments(self, limit=10):
        appts = _read_json(FILES["appointments"], [])
        me = current_doctor()
        from datetime import datetime
        now = datetime.now().isoformat()
        rows = [a for a in appts if a["doctor_id"]==me["id"] and a["start"] >= now]
        rows.sort(key=lambda x: x["start"])
        return rows[:limit]

    # --- Patients ---
    def list_assigned_or_consented_patients(self):
        me = current_doctor()
        patients = _read_json(FILES["patients"], [])
        rows = []
        for p in patients:
            if (me["id"] in p.get("assigned_doctor_ids", [])) or p.get("consent_to_all_doctors"):
                rows.append({"id":p["id"], "name":p["name"], "contact":p["contact"]})
        return rows

    # --- Files/Uploads ---
    def save_upload(self, patient_id: str, filename: str, content: bytes) -> str:
        path = (UPLOAD_DIR / f"{patient_id}_{filename}").as_posix()
        with open(path, "wb") as f:
            f.write(content)
        # index into patient record
        pats = _read_json(FILES["patients"], [])
        for p in pats:
            if p["id"] == patient_id:
                p.setdefault("uploads", []).append(path)
        _write_json(FILES["patients"], pats)
        self.audit("attachment.upload", target=patient_id)
        return path

    # --- Audit ---
    def audit(self, action: str, target: str = "", extra: dict | None = None):
        me = current_doctor()
        rec = {
            "timestamp": datetime.now().isoformat(),
            "user_id": me.get("id","?"),
            "action": action,
            "target": target,
            "extra": extra or {}
        }
        with open(FILES["audit"], "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
