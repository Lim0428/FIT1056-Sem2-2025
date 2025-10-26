# counselor_name_app/services/appointments.py
from typing import Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from counselor_name_app.repository import Repo

class AppointmentService:
    def __init__(self, repo: Optional[Repo] = None):
        self.repo = repo or Repo()

    def _parse(self, iso: str) -> datetime:
        # Accepts 'YYYY-MM-DDTHH:MM[:SS[.ffffff]]'
        return datetime.fromisoformat(iso)

    # --- Queries ---
    def list_for_counselor(self, counselor_id: str) -> List[Dict]:
        return [
            a for a in self.repo.read().get("appointments", {}).values()
            if a.get("counselor_id") == counselor_id
        ]

    def list_for_patient(self, patient_id: str) -> List[Dict]:
        return [
            a for a in self.repo.read().get("appointments", {}).values()
            if a.get("patient_id") == patient_id
        ]

    # --- Logic ---
    def _conflict(self, counselor_id: str, start_iso: str, end_iso: str) -> bool:
        start = self._parse(start_iso); end = self._parse(end_iso)
        for ap in self.list_for_counselor(counselor_id):
            s = self._parse(ap["start"]); e = self._parse(ap["end"])
            # overlap when latest start < earliest end
            if max(s, start) < min(e, end):
                return True
        return False

    # --- Commands ---
    def book(self, patient_id: str, counselor_id: str, start_iso: str, end_iso: str, kind: str) -> Dict:
        if self._conflict(counselor_id, start_iso, end_iso):
            raise ValueError("Time conflict – choose another slot.")
        db = self.repo.read()
        aid = "A-" + uuid4().hex[:8]
        ap = {
            "id": aid,
            "patient_id": patient_id,
            "counselor_id": counselor_id,
            "start": start_iso,
            "end": end_iso,
            "kind": kind,
            "status": "Booked",
        }
        db.setdefault("appointments", {})[aid] = ap
        self.repo.write(db)
        return ap
