# medical_staff/app/medical_staff_service.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import os, json

from .data_backend import PATHS, jread, jwrite, jappend_audit, bump_seq

def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

def _norm(s) -> str:
    return (s or "").strip().lower()

def _as_list(x, default=[]):  # noqa: B006
    return x if isinstance(x, list) else list(default)

def _coerce_patient_value(pid: str, v: Any) -> Dict[str, Any]:
    """
    Make a robust patient dict out of any value shape.
    - If v is a dict -> shallow copy
    - If v is a sequence of pairs -> dict(v)
    - If v is a sequence of scalars -> put as medical_details
    - Otherwise -> str(v) as name
    Always ensure row['id'] = pid (if pid provided).
    """
    row: Dict[str, Any] = {}
    if isinstance(v, dict):
        row = dict(v)
    elif isinstance(v, (list, tuple)):
        # Try interpreting as list of (key,value) pairs
        ok = False
        try:
            tmp = dict(v)  # works only if each element is 2-long
            if isinstance(tmp, dict) and tmp:
                row = tmp
                ok = True
        except Exception:
            ok = False
        if not ok:
            # Fall back: treat as a list of scalars; stash as details
            row = {
                "name": str(v[0]) if v and not isinstance(v[0], (list, tuple, dict)) else "",
                "medical_details": ", ".join(map(lambda x: str(x), v))
            }
    elif v is None:
        row = {}
    else:
        # scalar -> treat as name
        row = {"name": str(v)}
    # Ensure ID is set
    if pid:
        row.setdefault("id", pid)
    elif "id" not in row:
        # if no pid provided (list storage), try to keep existing id or generate placeholder
        row["id"] = row.get("id", "").strip() or f"PX-{abs(hash(json.dumps(row, sort_keys=True)))%1000000:06d}"
    return row

def _rows_from_patients_store(raw: Any) -> List[Dict[str, Any]]:
    """
    Accept either:
      - dict keyed by patient ID
      - list of patient-like entries
    Be forgiving on inner value shapes.
    """
    if isinstance(raw, dict):
        out: List[Dict[str, Any]] = []
        for pid, v in raw.items():
            out.append(_coerce_patient_value(str(pid), v))
        return out
    # list mode
    return [ _coerce_patient_value("", v) for v in (raw or []) ]

class MedicalStaffService:
    """
    Storage-backed service targeting /data. Uses patient.json (fixed),
    and is robust to mixed/legacy shapes inside that file.
    """

    # ---------------- Patients ----------------
    def list_patients(self, assigned_to: Optional[str] = None) -> List[Dict[str, Any]]:
        raw = jread("patients", [])
        patients = _rows_from_patients_store(raw)
        if assigned_to:
            staff = self.get_staff(assigned_to)
            if staff:
                allowed = set(staff.get("assigned_patients", []))
                patients = [p for p in patients if p.get("id") in allowed]
        return patients

    def search_patients(self, q: str, assigned_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Case-insensitive partial search across:
          id, name, mrn, medical_record, medical_record_number, medical_details
        """
        qn = _norm(q)
        rows = self.list_patients(assigned_to=assigned_to)
        if not qn:
            return rows
        keys = ("id", "name", "mrn", "medical_record", "medical_record_number", "medical_details")
        out: List[Dict[str, Any]] = []
        for p in rows:
            for k in keys:
                if qn in _norm(p.get(k, "")):
                    out.append(p)
                    break
        return out

    # ---------------- Staff (directory/assignments) ----------------
    def list_staff(self) -> List[Dict[str, Any]]:
        return _as_list(jread("staff", []))

    def get_staff(self, staff_id: str) -> Optional[Dict[str, Any]]:
        sid = (staff_id or "").strip()
        for s in self.list_staff():
            if (s.get("id") or "").strip() == sid:
                return s
        return None

    # ---------------- Appointments ----------------
    def list_appointments(self, for_patient: Optional[str] = None,
                          from_iso: Optional[str] = None, to_iso: Optional[str] = None) -> List[Dict[str, Any]]:
        appts = _as_list(jread("appointments", []))
        out = []
        t0 = datetime.fromisoformat(from_iso) if from_iso else None
        t1 = datetime.fromisoformat(to_iso)   if to_iso   else None
        for a in appts:
            if (a.get("status") or "scheduled").lower() == "canceled":
                continue
            if for_patient and a.get("patient_id") != for_patient:
                continue
            iso = a.get("when") or a.get("datetime")
            if not iso:
                continue
            try:
                dt = datetime.fromisoformat(iso)
            except Exception:
                continue
            if t0 and dt < t0:
                continue
            if t1 and dt > t1:
                continue
            out.append(a)
        return sorted(out, key=lambda x: x.get("when", ""))

    def book_appointment(self, staff_id: str, patient_id: str, when_iso: str, note: str = "") -> Dict[str, Any]:
        appts = _as_list(jread("appointments", []))
        appt_id = f"A{int(bump_seq('appt')):06d}"
        row = {
            "id": appt_id,
            "patient_id": patient_id,
            "when": when_iso,
            "datetime": when_iso,       # compatibility
            "note": note,
            "created_by": staff_id,
            "status": "scheduled",
        }
        appts.append(row)
        jwrite("appointments", appts)
        jappend_audit(staff_id, "appointment.book", patient_id, f"{when_iso} | {note}")
        return row

    def reschedule_appointment(self, appt_id: str, new_iso_dt: str, who: str) -> bool:
        appts = _as_list(jread("appointments", [])); ok = False
        for a in appts:
            if a.get("id") == appt_id:
                a["when"] = new_iso_dt
                a["datetime"] = new_iso_dt
                ok = True
                break
        if ok:
            jwrite("appointments", appts)
            jappend_audit(who, "appointment.reschedule", appt_id, new_iso_dt)
        return ok

    def cancel_appointment(self, appt_id: str, who: str) -> bool:
        appts = _as_list(jread("appointments", [])); ok = False
        for a in appts:
            if a.get("id") == appt_id:
                a["status"] = "canceled"
                ok = True
                break
        if ok:
            jwrite("appointments", appts)
            jappend_audit(who, "appointment.cancel", appt_id, "")
        return ok

    # ---------------- Messages ----------------
    def list_messages_for_patient(self, patient_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        msgs = [m for m in _as_list(jread("messages", [])) if m.get("patient_id") == patient_id]
        msgs.sort(key=lambda x: x.get("timestamp", ""))
        return msgs[-limit:]

    def send_message_to_patient(self, staff_id: str, patient_id: str, text: str) -> Dict[str, Any]:
        msgs = _as_list(jread("messages", []))
        mid = f"M{int(bump_seq('msg')):06d}"
        row = {"id": mid, "timestamp": _now_iso(), "from_role": "staff",
               "staff_id": staff_id, "patient_id": patient_id, "text": text}
        msgs.append(row)
        jwrite("messages", msgs)
        jappend_audit(staff_id, "msg.send", patient_id, text[:120])
        return row

    # ---------------- Encounters (vitals / observations / MAR) ----------------
    def add_vitals(self, staff_id: str, patient_id: str, **kwargs) -> Dict[str, Any]:
        enc = _as_list(jread("encounters", []))
        eid = f"E{int(bump_seq('enc')):06d}"
        row = {"id": eid, "kind": "vitals", "timestamp": _now_iso(),
               "staff_id": staff_id, "patient_id": patient_id, **kwargs}
        enc.append(row)
        jwrite("encounters", enc)
        jappend_audit(staff_id, "vitals.add", patient_id, "")
        return row

    def list_vitals(self, patient_id: str, days: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        enc = [e for e in _as_list(jread("encounters", []))
               if e.get("kind") == "vitals" and e.get("patient_id") == patient_id]
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            enc = [e for e in enc if datetime.fromisoformat(e.get("timestamp", "1970-01-01")) >= cutoff]
        enc.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return enc[:limit]

    def record_observation(self, staff_id: str, patient_id: str, **kwargs) -> Dict[str, Any]:
        enc = _as_list(jread("encounters", []))
        eid = f"E{int(bump_seq('enc')):06d}"
        row = {"id": eid, "kind": "observation", "timestamp": _now_iso(),
               "staff_id": staff_id, "patient_id": patient_id, **kwargs}
        enc.append(row)
        jwrite("encounters", enc)
        jappend_audit(staff_id, "observation.add", patient_id, "")
        return row

    def list_observations(self, patient_id: str, days: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        enc = [e for e in _as_list(jread("encounters", []))
               if e.get("kind") == "observation" and e.get("patient_id") == patient_id]
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            enc = [e for e in enc if datetime.fromisoformat(e.get("timestamp", "1970-01-01")) >= cutoff]
        enc.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return enc[:limit]

    def add_med_admin(self, staff_id: str, patient_id: str, drug: str, dose: str, route: str,
                      time_sched: str, given: bool, note: str = "") -> Dict[str, Any]:
        enc = _as_list(jread("encounters", []))
        eid = f"E{int(bump_seq('enc')):06d}"
        row = {"id": eid, "kind": "med_admin", "timestamp": _now_iso(),
               "staff_id": staff_id, "patient_id": patient_id,
               "drug": drug, "dose": dose, "route": route,
               "schedule": time_sched, "given": bool(given), "note": note}
        enc.append(row)
        jwrite("encounters", enc)
        jappend_audit(staff_id, "mar.add", patient_id, f"{drug} {dose} {route} @ {time_sched}")
        return row

    def list_med_admin(self, patient_id: str, days: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        enc = [e for e in _as_list(jread("encounters", []))
               if e.get("kind") == "med_admin" and e.get("patient_id") == patient_id]
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            enc = [e for e in enc if datetime.fromisoformat(e.get("timestamp", "1970-01-01")) >= cutoff]
        enc.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return enc[:limit]

    # ---------------- Tasks ----------------
    def add_task(self, staff_id: str, patient_id: str, title: str, due_iso: str, note: str = "") -> Dict[str, Any]:
        rows = _as_list(jread("tasks", []))
        tid = f"T{int(bump_seq('task')):06d}"
        row = {"id": tid, "created_at": _now_iso(), "due_date": due_iso, "patient_id": patient_id,
               "staff_id": staff_id, "title": title, "done": False, "note": note}
        rows.append(row)
        jwrite("tasks", rows)
        jappend_audit(staff_id, "task.add", patient_id, title)
        return row

    def list_tasks(self, patient_id: Optional[str], include_done: bool = True) -> List[Dict[str, Any]]:
        rows = _as_list(jread("tasks", []))
        if patient_id:
            rows = [t for t in rows if t.get("patient_id") == patient_id]
        if not include_done:
            rows = [t for t in rows if not t.get("done", False)]
        rows.sort(key=lambda x: (x.get("done", False), x.get("due_date", "")))
        return rows

    def set_task_done(self, task_id: str, done: bool, who: str) -> bool:
        rows = _as_list(jread("tasks", [])); ok = False
        for t in rows:
            if t.get("id") == task_id:
                t["done"] = bool(done)
                ok = True
                break
        if ok:
            jwrite("tasks", rows)
            jappend_audit(who, "task.done" if done else "task.undone", task_id, "")
        return ok

    # ---------------- Handover ----------------
    def add_handover(self, staff_id: str, patient_id: str, shift: str, summary: str) -> Dict[str, Any]:
        rows = _as_list(jread("handover", []))
        row = {"id": f"H{int(bump_seq('enc')):06d}", "timestamp": _now_iso(),
               "staff_id": staff_id, "patient_id": patient_id, "shift": shift, "summary": summary}
        rows.append(row)
        jwrite("handover", rows)
        jappend_audit(staff_id, "handover.add", patient_id, shift)
        return row

    def list_handover(self, patient_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        rows = [h for h in _as_list(jread("handover", [])) if h.get("patient_id") == patient_id]
        rows.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return rows[:limit]

    # ---------------- Documents ----------------
    def add_document(self, staff_id: str, patient_id: str, filename: str, kind: str,
                     note: str, file_bytes: bytes) -> Dict[str, Any]:
        os.makedirs(os.path.join(PATHS["uploads_dir"], patient_id), exist_ok=True)
        idx = bump_seq("doc")
        stored = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}_{os.path.basename(filename)}"
        full_path = os.path.join(PATHS["uploads_dir"], patient_id, stored)
        with open(full_path, "wb") as f:
            f.write(file_bytes)

        docs = _as_list(jread("documents", []))
        did = f"D{int(idx):06d}"
        meta = {"id": did, "uploaded_at": _now_iso(), "staff_id": staff_id, "patient_id": patient_id,
                "name": filename, "stored_name": stored, "kind": kind, "note": note}
        docs.append(meta)
        jwrite("documents", docs)
        jappend_audit(staff_id, "doc.add", patient_id, f"{kind} | {filename}")
        return meta

    def list_documents(self, patient_id: str, kind: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        docs = [d for d in _as_list(jread("documents", [])) if d.get("patient_id") == patient_id]
        if kind:
            docs = [d for d in docs if (d.get("kind") or "").lower() == kind.lower()]
        docs.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
        return docs[:limit]

    # ---------------- Audit (read JSONL) ----------------
    def list_audit(self, who: Optional[str] = None, patient_id: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        path = PATHS["audit_log"]
        if not os.path.exists(path):
            return []
        rows: List[Dict[str, Any]] = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    rows.append(obj)
        except Exception:
            return []
        if who:
            rows = [r for r in rows if r.get("who") == who]
        if patient_id:
            rows = [r for r in rows if (patient_id in (r.get("target", "") + r.get("detail", "")))]
        rows.sort(key=lambda x: x.get("when", ""), reverse=True)
        return rows[:limit]
