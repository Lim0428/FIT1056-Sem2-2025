# doctor_name_services/data_store.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Any, Dict, List
from doctor_name_services.auth import current_doctor

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

def _read_json(path: Path, default: Any):
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f: json.dump(default, f, indent=2)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except Exception:
        return default

def _write_json(path: Path, data: Any):
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)

def _normalize_appointments(raw):
    if isinstance(raw, dict) and isinstance(raw.get("appointments"), list): items=raw["appointments"]
    elif isinstance(raw, list): items=raw
    else: items=[]
    return [a for a in items if isinstance(a, dict)]

class DataStore:
    def __init__(self):
        _read_json(FILES["doctors"], [{
            "id":"doc1","email":"doc@example.com","password":"pass123",
            "safety_q":"pet?","safety_a":"milo","specialty":"General Medicine",
            "qualifications":"MBBS","license_no":"D-001","working_hours":"Mon–Fri 9:00–17:00",
            "contact":"+60-12-345-6789"
        }])
        _read_json(FILES["patients"], [])
        _read_json(FILES["appointments"], [])
        _read_json(FILES["messages"], [])
        _read_json(FILES["encounters"], [])
        if not FILES["audit"].exists(): FILES["audit"].write_text("", encoding="utf-8")
        self._appointments = _normalize_appointments(_read_json(FILES["appointments"], []))

    def reload_appointments(self):
        self._appointments = _normalize_appointments(_read_json(FILES["appointments"], []))

    # Stats
    def doctor_display_name(self) -> str:
        me_id = current_doctor().get("id"); docs = _read_json(FILES["doctors"], [])
        for d in docs:
            if d.get("id")==me_id:
                return d.get("name") or d.get("email") or f"Doctor {me_id}"
        return "Doctor"

    def doctor_average_rating(self) -> tuple[float, int]:
        me_id = current_doctor().get("id"); pts = _read_json(FILES["patients"], [])
        scores=[]; 
        for p in pts:
            for r in p.get("ratings", []):
                if r.get("doctor_id")==me_id and isinstance(r.get("score"),(int,float)):
                    scores.append(float(r["score"]))
        if not scores: return (0.0,0)
        return (round(sum(scores)/len(scores),1), len(scores))

    def count_assigned_patients(self) -> int:
        me = current_doctor(); patients = _read_json(FILES["patients"], [])
        return sum(1 for p in patients if (me.get("id") in p.get("assigned_doctor_ids", [])) or p.get("consent_to_all_doctors", False))

    def count_today_appts(self) -> int:
        me = current_doctor(); today=date.today().isoformat()
        appts=_normalize_appointments(_read_json(FILES["appointments"], []))
        n=0
        for a in appts:
            if not isinstance(a, dict): continue
            if me and a.get("doctor_id")!=me.get("id"): continue
            if str(a.get("start",""))[:10]==today: n+=1
        return n

    def count_unread_messages(self) -> int:
        threads = _read_json(FILES["messages"], [])
        me = current_doctor()
        return sum(1 for t in threads if t.get("doctor_id")==me.get("id") and t.get("status")=="open")

    def count_recent_edits(self) -> int:
        encs = _read_json(FILES["encounters"], [])
        cutoff = datetime.now() - timedelta(days=7); count=0
        for e in encs:
            for v in e.get("versions", []):
                try:
                    if datetime.fromisoformat(v.get("timestamp",""))>=cutoff: count+=1; break
                except: pass
        return count

    def list_upcoming_appointments(self, limit: int = 10) -> List[Dict[str, Any]]:
        appts=_normalize_appointments(_read_json(FILES["appointments"], []))
        me=current_doctor(); now_iso=datetime.now().isoformat()
        rows=[a for a in appts if a.get("doctor_id")==me.get("id") and a.get("start","")>=now_iso]
        rows.sort(key=lambda x:x.get("start",""))
        return rows[:limit]

    def list_all_appointments(self) -> List[Dict[str, Any]]:
        return list(self._appointments)

    def audit(self, action: str, target: str = "", extra: dict | None = None):
        me=current_doctor()
        rec={"timestamp":datetime.now().isoformat(),"user_id":me.get("id","?"),"action":action,"target":target,"extra":extra or {}}
        with open(FILES["audit"],"a",encoding="utf-8") as f: f.write(json.dumps(rec)+"\n")
