# nurse/app/nurse_service.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .repository import Repo, _now_iso

NURSE_ID = "nurse_001"  # no login yet

class NurseService:
    def __init__(self, repo: Optional[Repo] = None):
        self.repo = repo or Repo()

    # Patients
    def list_patients(self, *, assigned_to: Optional[str] = NURSE_ID) -> List[Dict[str, Any]]:
        rows = self.repo.list("patients")
        if assigned_to:
            rows = [p for p in rows if p.get("assigned_to") == assigned_to]
        return sorted(rows, key=lambda p: p["name"])

    # Vitals & Notes
    def record_vitals(self, patient_id: str, vitals: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            "id": self.repo.next_id("v", "vitals"),
            "patient_id": patient_id,
            "taken_at": vitals.get("taken_at") or _now_iso(),
            "bp": vitals.get("bp"),
            "hr": vitals.get("hr"),
            "temp": vitals.get("temp"),
            "spo2": vitals.get("spo2"),
            "pain": vitals.get("pain"),
            "note": vitals.get("note", ""),
            "author_id": NURSE_ID,
        }
        return self.repo.upsert("vitals", row)

    def add_note(self, patient_id: str, text: str) -> Dict[str, Any]:
        row = {
            "id": self.repo.next_id("n", "notes"),
            "patient_id": patient_id,
            "created_at": _now_iso(),
            "text": text,
            "author_id": NURSE_ID,
        }
        return self.repo.upsert("notes", row)

    def list_vitals(self, patient_id: str) -> List[Dict[str, Any]]:
        return [v for v in self.repo.list("vitals") if v["patient_id"] == patient_id]

    def list_notes(self, patient_id: str) -> List[Dict[str, Any]]:
        return [n for n in self.repo.list("notes") if n["patient_id"] == patient_id]

    # MAR
    def log_med_admin(self, patient_id: str, *, drug: str, dose: str, route: str,
                      time_iso: Optional[str] = None) -> Dict[str, Any]:
        row = {
            "id": self.repo.next_id("m", "mar"),
            "patient_id": patient_id,
            "drug": drug, "dose": dose, "route": route,
            "time": time_iso or _now_iso(),
            "author_id": NURSE_ID,
        }
        return self.repo.upsert("mar", row)

    def get_mar(self, patient_id: str) -> List[Dict[str, Any]]:
        return [m for m in self.repo.list("mar") if m["patient_id"] == patient_id]

    # Tasks
    def list_tasks(self, *, only_my=True) -> List[Dict[str, Any]]:
        tasks = self.repo.list("tasks")
        if only_my:
            tasks = [t for t in tasks if t.get("assignee_id") == NURSE_ID]
        order = {"high": 0, "medium": 1, "low": 2}
        return sorted(tasks, key=lambda t: (order.get(t.get("priority", "medium"), 1), t.get("due_at", "")))

    def add_task(self, title: str, due_at: str, priority: str = "medium",
                 patient_id: Optional[str] = None) -> Dict[str, Any]:
        row = {
            "id": self.repo.next_id("t", "tasks"),
            "title": title, "due_at": due_at, "priority": priority,
            "patient_id": patient_id, "status": "pending", "assignee_id": NURSE_ID,
        }
        return self.repo.upsert("tasks", row)

    def complete_task(self, task_id: str) -> bool:
        tasks = self.repo.list("tasks")
        for t in tasks:
            if t["id"] == task_id:
                t["status"] = "completed"
                self.repo.upsert("tasks", t)
                return True
        return False

    # Notifications
    def list_notifications(self) -> List[Dict[str, Any]]:
        return self.repo.list("notifications")

    def ack_notification(self, notif_id: str) -> bool:
        rows = self.repo.list("notifications")
        for n in rows:
            if n["id"] == notif_id:
                n["status"] = "read"
                self.repo.upsert("notifications", n)
                return True
        return False

    # Messaging
    def list_messages(self, *, status: Optional[str] = None) -> List[Dict[str, Any]]:
        msgs = self.repo.list("messages")
        if status:
            msgs = [m for m in msgs if m.get("status") == status]
        return sorted(msgs, key=lambda m: m.get("created_at", ""))

    def send_message(self, text: str, to_role: str, to_id: Optional[str] = None,
                     patient_id: Optional[str] = None) -> Dict[str, Any]:
        row = {
            "id": self.repo.next_id("msg", "messages"),
            "created_at": _now_iso(),
            "from": {"role": "nurse", "id": NURSE_ID},
            "to_role": to_role, "to_id": to_id,
            "text": text, "patient_id": patient_id,
            "status": "sent",
        }
        return self.repo.upsert("messages", row)

    # Appointments (30-min slots; no past)
    def list_appointments(self, *, patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        appts = self.repo.list("appointments")
        if patient_id:
            appts = [a for a in appts if a["patient_id"] == patient_id]
        return sorted(appts, key=lambda a: a["start"])

    def _floor_to_half_hour(self, dt: datetime) -> datetime:
        minute = 0 if dt.minute < 30 else 30
        return dt.replace(minute=minute, second=0, microsecond=0)

    def book_appointment(self, patient_id: str, clinician_id: str, start: datetime,
                         *, clinician_role: str = "doctor", note: str = "") -> Dict[str, Any]:
        start = self._floor_to_half_hour(start)
        if start < datetime.utcnow():
            raise ValueError("Cannot book in the past.")
        end = start + timedelta(minutes=30)
        for a in self.repo.list("appointments"):
            if a["clinician_id"] == clinician_id and a["status"] != "cancelled":
                if not (end <= datetime.fromisoformat(a["start"]) or start >= datetime.fromisoformat(a["end"])):
                    raise ValueError("Time slot already booked.")
        row = {
            "id": self.repo.next_id("a", "appointments"),
            "patient_id": patient_id, "clinician_id": clinician_id,
            "clinician_role": clinician_role,
            "start": start.replace(microsecond=0).isoformat(),
            "end": end.replace(microsecond=0).isoformat(),
            "status": "booked", "note": note,
        }
        return self.repo.upsert("appointments", row)

    def cancel_appointment(self, appt_id: str) -> bool:
        appts = self.repo.list("appointments")
        for a in appts:
            if a["id"] == appt_id:
                a["status"] = "cancelled"
                self.repo.upsert("appointments", a)
                return True
        return False

    def reschedule_appointment(self, appt_id: str, new_start: datetime) -> Dict[str, Any]:
        appts = self.repo.list("appointments")
        target = next((a for a in appts if a["id"] == appt_id), None)
        if not target:
            raise ValueError("Appointment not found.")
        self.cancel_appointment(appt_id)
        return self.book_appointment(target["patient_id"], target["clinician_id"], new_start,
                                     clinician_role=target["clinician_role"], note=target.get("note", ""))
