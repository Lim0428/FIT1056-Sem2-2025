# app/medical_staff.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import os
from pathlib import Path
from app.storage import read_db, write_db, ensure_db

CARELOG_PATH = "data/carelog.json"           # main shared DB (patients, appts, messages)
OBS_PATH     = "data/observations.json"      # daily clinical observations
VITALS_PATH  = "data/vitals.json"            # vitals history
MEDS_PATH    = "data/meds.json"              # medication administration record (MAR)
TASKS_PATH   = "data/tasks.json"             # staff tasks/checklists per patient
HANDOVER_PATH= "data/handover.json"          # shift handover notes
DOCS_PATH    = "data/documents.json"         # uploaded docs metadata (file saved in data/docs/)
AUDIT_PATH   = "data/audit.json"             # audit trail

Path("data/docs").mkdir(parents=True, exist_ok=True)

# ------------------------------ Data models ------------------------------
@dataclass
class Observation:
    timestamp: str
    staff_id: str
    patient_id: str
    mood: str
    pain: int
    sleep: str
    appetite: str
    notes: str

@dataclass
class Vitals:
    timestamp: str
    staff_id: str
    patient_id: str
    temp_c: float
    systolic: int
    diastolic: int
    hr: int
    rr: int
    spo2: int

@dataclass
class MedAdmin:
    timestamp: str
    staff_id: str
    patient_id: str
    med_name: str
    dose: str
    route: str
    schedule: str
    given: bool
    note: str

@dataclass
class TaskItem:
    id: str
    created_at: str
    due_date: str
    patient_id: str
    staff_id: str
    title: str
    done: bool
    note: str

@dataclass
class HandoverNote:
    timestamp: str
    staff_id: str
    patient_id: str
    shift: str
    summary: str

@dataclass
class DocMeta:
    id: str
    uploaded_at: str
    staff_id: str
    patient_id: str
    name: str
    path: str
    kind: str
    note: str

@dataclass
class AuditEntry:
    when: str
    who: str
    action: str
    target: str
    detail: str


# ------------------------------ Service ------------------------------
class MedicalStaffService:
    """
    Medical Staff service layer: patients, observations, vitals, meds (MAR),
    tasks, handover, appointments, messages, documents, audit trail.
    """

    def __init__(self,
                 carelog: str = CARELOG_PATH,
                 obs: str = OBS_PATH,
                 vitals: str = VITALS_PATH,
                 meds: str = MEDS_PATH,
                 tasks: str = TASKS_PATH,
                 handover: str = HANDOVER_PATH,
                 docs: str = DOCS_PATH,
                 audit: str = AUDIT_PATH):
        self.carelog = carelog
        self.obs = obs
        self.vitals = vitals
        self.meds = meds
        self.tasks = tasks
        self.handover = handover
        self.docs = docs
        self.audit = audit

        ensure_db(self.carelog, {"patients": [], "appointments": [], "messages": []})
        ensure_db(self.obs, {"observations": []})
        ensure_db(self.vitals, {"vitals": []})
        ensure_db(self.meds, {"mar": []})
        ensure_db(self.tasks, {"tasks": []})
        ensure_db(self.handover, {"handover": []})
        ensure_db(self.docs, {"docs": []})
        ensure_db(self.audit, {"audit": []})

    # ---------- Patients ----------
    def list_patients(self, assigned_to: Optional[str] = None) -> List[Dict[str, Any]]:
        db = read_db(self.carelog)
        pts = db.get("patients", [])
        if assigned_to:
            return [p for p in pts if p.get("assigned_staff_id") == assigned_to]
        return pts

    def search_patients(self, q: str, assigned_to: Optional[str] = None) -> List[Dict[str, Any]]:
        qn = q.strip().lower()
        base = self.list_patients(assigned_to)
        if not qn:
            return base
        out = []
        for p in base:
            if any(qn in str(p.get(k, "")).lower() for k in ("id", "name", "contact", "phone", "email")):
                out.append(p)
        return out

    # ---------- Observations ----------
    def record_observation(self, staff_id: str, patient_id: str,
                           mood: str, pain: int, sleep: str, appetite: str, notes: str) -> Observation:
        db = read_db(self.obs)
        item = Observation(
            timestamp=_now(),
            staff_id=staff_id,
            patient_id=patient_id,
            mood=mood,
            pain=int(pain),
            sleep=sleep,
            appetite=appetite,
            notes=notes.strip(),
        )
        db["observations"].append(asdict(item))
        write_db(self.obs, db)
        self._audit(staff_id, "observation.add", patient_id, f"mood={mood}, pain={pain}")
        return item

    def list_observations(self, patient_id: str, days: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        db = read_db(self.obs)
        items = [o for o in db.get("observations", []) if o.get("patient_id") == patient_id]
        if days:
            cutoff = _parse_dt(_now()) - timedelta(days=days)
            items = [o for o in items if _parse_dt(o["timestamp"]) >= cutoff]
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return items[:limit]

    # ---------- Vitals ----------
    def add_vitals(self, staff_id: str, patient_id: str, temp_c: float, systolic: int, diastolic: int,
                   hr: int, rr: int, spo2: int) -> Vitals:
        db = read_db(self.vitals)
        v = Vitals(
            timestamp=_now(),
            staff_id=staff_id,
            patient_id=patient_id,
            temp_c=float(temp_c),
            systolic=int(systolic),
            diastolic=int(diastolic),
            hr=int(hr), rr=int(rr), spo2=int(spo2)
        )
        db["vitals"].append(asdict(v))
        write_db(self.vitals, db)
        self._audit(staff_id, "vitals.add", patient_id, f"BP {systolic}/{diastolic}, HR {hr}, SpO2 {spo2}")
        return v

    def list_vitals(self, patient_id: str, days: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        db = read_db(self.vitals)
        items = [v for v in db.get("vitals", []) if v.get("patient_id") == patient_id]
        if days:
            cutoff = _parse_dt(_now()) - timedelta(days=days)
            items = [v for v in items if _parse_dt(v["timestamp"]) >= cutoff]
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return items[:limit]

    # ---------- Medications (MAR) ----------
    def add_med_admin(self, staff_id: str, patient_id: str, med_name: str, dose: str,
                      route: str, schedule: str, given: bool, note: str) -> MedAdmin:
        db = read_db(self.meds)
        m = MedAdmin(
            timestamp=_now(),
            staff_id=staff_id,
            patient_id=patient_id,
            med_name=med_name.strip(),
            dose=dose.strip(),
            route=route.strip(),
            schedule=schedule.strip(),
            given=bool(given),
            note=note.strip(),
        )
        db["mar"].append(asdict(m))
        write_db(self.meds, db)
        self._audit(staff_id, "meds.admin", patient_id, f"{med_name} {dose} {route} {schedule} given={given}")
        return m

    def list_med_admin(self, patient_id: str, days: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        db = read_db(self.meds)
        items = [m for m in db.get("mar", []) if m.get("patient_id") == patient_id]
        if days:
            cutoff = _parse_dt(_now()) - timedelta(days=days)
            items = [m for m in items if _parse_dt(m["timestamp"]) >= cutoff]
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return items[:limit]

    # ---------- Tasks / Checklists ----------
    def add_task(self, staff_id: str, patient_id: str, title: str, due_date_iso: str, note: str = "") -> TaskItem:
        db = read_db(self.tasks)
        tid = f"T{int(datetime.now().timestamp())}"
        t = TaskItem(
            id=tid,
            created_at=_now(),
            due_date=due_date_iso,
            patient_id=patient_id,
            staff_id=staff_id,
            title=title.strip(),
            done=False,
            note=note.strip(),
        )
        db["tasks"].append(asdict(t))
        write_db(self.tasks, db)
        self._audit(staff_id, "task.add", patient_id, title)
        return t

    def list_tasks(self, patient_id: str, include_done: bool = True) -> List[Dict[str, Any]]:
        db = read_db(self.tasks)
        items = [t for t in db.get("tasks", []) if t.get("patient_id") == patient_id]
        if not include_done:
            items = [t for t in items if not t.get("done", False)]
        items.sort(key=lambda x: (x.get("done", False), x.get("due_date","")))
        return items

    def set_task_done(self, task_id: str, done: bool, who: str) -> Tuple[bool, str]:
        db = read_db(self.tasks)
        changed = False
        for t in db.get("tasks", []):
            if t["id"] == task_id:
                t["done"] = bool(done)
                changed = True
                break
        if changed:
            write_db(self.tasks, db)
            self._audit(who, "task.set_done", task_id, f"done={done}")
            return True, "Updated"
        return False, "Task not found"

    # ---------- Handover ----------
    def add_handover(self, staff_id: str, patient_id: str, shift: str, summary: str) -> HandoverNote:
        db = read_db(self.handover)
        h = HandoverNote(
            timestamp=_now(),
            staff_id=staff_id,
            patient_id=patient_id,
            shift=shift,
            summary=summary.strip(),
        )
        db["handover"].append(asdict(h))
        write_db(self.handover, db)
        self._audit(staff_id, "handover.add", patient_id, f"shift={shift}")
        return h

    def list_handover(self, patient_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        db = read_db(self.handover)
        items = [h for h in db.get("handover", []) if h.get("patient_id") == patient_id]
        items.sort(key=lambda x: x.get("timestamp",""), reverse=True)
        return items[:limit]

    # ---------- Appointments ----------
    def list_appointments(self, for_patient: Optional[str] = None,
                          from_iso: Optional[str] = None, to_iso: Optional[str] = None) -> List[Dict[str, Any]]:
        db = read_db(self.carelog)
        appts = db.get("appointments", [])
        if for_patient:
            appts = [a for a in appts if a.get("patient_id") == for_patient]
        if from_iso:
            fr = _parse_dt(from_iso)
            appts = [a for a in appts if _parse_dt(a.get("dt")) >= fr]
        if to_iso:
            to = _parse_dt(to_iso)
            appts = [a for a in appts if _parse_dt(a.get("dt")) <= to]
        appts.sort(key=lambda a: a.get("dt", ""))
        return appts

    def reschedule_appointment(self, appt_id: str, new_iso_dt: str, who: str) -> Tuple[bool, str]:
        db = read_db(self.carelog)
        for a in db.get("appointments", []):
            if a.get("id") == appt_id:
                a["dt"] = new_iso_dt
                a["status"] = "rescheduled"
                write_db(self.carelog, db)
                self._audit(who, "appt.reschedule", appt_id, f"to={new_iso_dt}")
                return True, "Appointment rescheduled."
        return False, "Appointment not found."

    def cancel_appointment(self, appt_id: str, who: str) -> Tuple[bool, str]:
        db = read_db(self.carelog)
        for a in db.get("appointments", []):
            if a.get("id") == appt_id:
                a["status"] = "cancelled"
                write_db(self.carelog, db)
                self._audit(who, "appt.cancel", appt_id, "")
                return True, "Appointment cancelled."
        return False, "Appointment not found."

    # ---------- Messages (two-way) ----------
    def list_messages_for_patient(self, patient_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        db = read_db(self.carelog)
        msgs = [m for m in db.get("messages", []) if m.get("to_patient_id") == patient_id or m.get("from_patient_id") == patient_id]
        msgs.sort(key=lambda m: m.get("timestamp",""), reverse=True)
        return msgs[:limit]

    def send_message_to_patient(self, staff_id: str, patient_id: str, text: str) -> Dict[str, Any]:
        db = read_db(self.carelog)
        msg = {
            "id": f"M{int(datetime.now().timestamp())}",
            "timestamp": _now(),
            "from_role": "staff",
            "from_staff_id": staff_id,
            "from_patient_id": None,
            "to_role": "patient",
            "to_patient_id": patient_id,
            "from_name": f"Staff {staff_id}",
            "text": text.strip(),
        }
        db.setdefault("messages", []).append(msg)
        write_db(self.carelog, db)
        self._audit(staff_id, "msg.send", patient_id, text[:60])
        return msg

    # ---------- Documents ----------
    def add_document(self, staff_id: str, patient_id: str, filename: str, kind: str, note: str, file_bytes: bytes) -> DocMeta:
        # Save file under data/docs/{patient_id}/{timestamp}_{filename}
        folder = Path("data/docs") / patient_id
        folder.mkdir(parents=True, exist_ok=True)
        ts = int(datetime.now().timestamp())
        safe_name = f"{ts}_{filename}".replace(" ", "_")
        out_path = folder / safe_name
        out_path.write_bytes(file_bytes)

        db = read_db(self.docs)
        doc = DocMeta(
            id=f"D{ts}",
            uploaded_at=_now(),
            staff_id=staff_id,
            patient_id=patient_id,
            name=filename,
            path=str(out_path.as_posix()),
            kind=kind,
            note=note.strip(),
        )
        db["docs"].append(asdict(doc))
        write_db(self.docs, db)
        self._audit(staff_id, "doc.upload", patient_id, f"{filename} ({kind})")
        return doc

    def list_documents(self, patient_id: str, kind: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        db = read_db(self.docs)
        items = [d for d in db.get("docs", []) if d.get("patient_id") == patient_id]
        if kind:
            items = [d for d in items if d.get("kind") == kind]
        items.sort(key=lambda x: x.get("uploaded_at",""), reverse=True)
        return items[:limit]

    # ---------- Audit ----------
    def _audit(self, who: str, action: str, target: str, detail: str):
        db = read_db(self.audit)
        db.setdefault("audit", []).append(asdict(AuditEntry(
            when=_now(), who=who, action=action, target=target, detail=detail
        )))
        write_db(self.audit, db)

    def list_audit(self, who: Optional[str] = None, patient_id: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        db = read_db(self.audit)
        items = db.get("audit", [])
        if who:
            items = [a for a in items if a.get("who") == who]
        if patient_id:
            items = [a for a in items if a.get("target") == patient_id or patient_id in a.get("detail","")]
        items.sort(key=lambda x: x.get("when",""), reverse=True)
        return items[:limit]


# ------------------------------ helpers ------------------------------
def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

def _parse_dt(s: Optional[str]) -> datetime:
    try:
        return datetime.fromisoformat(s)  # supports date or datetime ISO
    except Exception:
        return datetime.min
