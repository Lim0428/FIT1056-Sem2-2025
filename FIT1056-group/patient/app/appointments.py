# app/appointments.py
from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Tuple, Any
from app.storage import read_db, write_db


class AppointmentService:
    """
    Works with BOTH schemas stored at FIT1056-GROUP/data/appointments.json:

    Old (slot list):
      [
        {"id": "A000001", "patient_id": "P000001", "dt": "2025-10-24T11:00:00", "note": ""}
      ]

    New (patient-centric – your requested format):
      [
        {
          "id": "p1",
          "name": "...",
          "contact": "...",
          "assigned_doctor_ids": ["doc1"],
          "consent_to_all_doctors": false,
          "conditions": [...],
          "allergies": [...],
          "medications": [...],
          "history": [...],
          "treatments": [],
          "uploads": [],
          // OPTIONAL (created by this service when you start booking):
          "appointments": [
            {"id": "A000001", "dt": "2025-10-30T12:00:00", "note": ""}
          ],
          // OPTIONAL (auto-updated)
          "updated_at": "ISO-TS"
        }
      ]

    Public API preserved:
      - list_by_patient(patient_id) -> List[dict] in old-format shape
      - book(patient_id, when: datetime, note: str) -> (ok: bool, msg: str)
    """

    # ---------- utils ----------
    @staticmethod
    def _parse_dt(s: str | None) -> datetime | None:
        if not s or not isinstance(s, str):
            return None
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None

    def _load(self) -> Dict[str, Any]:
        db = read_db()
        appts = db.get("appointments")
        if not isinstance(appts, list):
            appts = []
        self._db = db
        self._raw = appts
        return db

    def _save(self) -> None:
        self._db["appointments"] = self._raw
        write_db(self._db)

    def _mode(self) -> str:
        """Detect schema: 'old' (flat slot list) or 'new' (patient-centric)."""
        for item in self._raw:
            if isinstance(item, dict):
                if "patient_id" in item and "dt" in item:
                    return "old"
                if "assigned_doctor_ids" in item or "consent_to_all_doctors" in item:
                    return "new"
        # default to 'new' if file empty and you want to use your new shape
        return "new"

    def _find_patient_row(self, patient_id: str) -> Dict[str, Any] | None:
        """Find a patient record in the new schema by id."""
        for row in self._raw:
            if isinstance(row, dict) and row.get("id") == patient_id:
                return row
        return None

    def _next_appt_id(self, db: Dict[str, Any]) -> str:
        seq = db.get("seq") or {}
        n = int(seq.get("appt", 1))
        appt_id = f"A{n:06d}"
        seq["appt"] = n + 1
        db["seq"] = seq
        return appt_id

    # ---------- queries ----------
    def list_by_patient(self, patient_id: str) -> List[dict]:
        """
        Return a normalized list of appointments for a patient:
        [{"id","patient_id","dt","note"}]
        Works on both schemas. If none found, returns [].
        """
        self._load()
        mode = self._mode()

        if mode == "old":
            # filter the flat slot list
            result = []
            for a in self._raw:
                if not isinstance(a, dict):
                    continue
                if a.get("patient_id") == patient_id and "dt" in a:
                    result.append({
                        "id": a.get("id"),
                        "patient_id": a.get("patient_id"),
                        "dt": a.get("dt"),
                        "note": a.get("note", ""),
                    })
            # sort by datetime ascending
            result.sort(key=lambda r: r.get("dt", ""))
            return result

        # mode == "new"
        row = self._find_patient_row(patient_id)
        if not row:
            return []
        appts = row.get("appointments") or []
        if not isinstance(appts, list):
            return []
        normalized = []
        for a in appts:
            if not isinstance(a, dict) or "dt" not in a:
                continue
            normalized.append({
                "id": a.get("id"),
                "patient_id": patient_id,
                "dt": a.get("dt"),
                "note": a.get("note", ""),
            })
        normalized.sort(key=lambda r: r.get("dt", ""))
        return normalized

    # ---------- mutations ----------
    def book(self, patient_id: str, when: datetime, note: str = "") -> Tuple[bool, str]:
        """
        Book a new appointment for patient_id at 'when'.
        In NEW schema: appended to that patient's 'appointments' list in data/appointments.json.
        In OLD schema: appended to the top-level list.
        """
        if not isinstance(when, datetime):
            return False, "Invalid time."

        db = self._load()
        mode = self._mode()

        # disallow past
        now = datetime.now()
        if when < now.replace(second=0, microsecond=0):
            return False, "Cannot book a past time."

        appt_id = self._next_appt_id(db)
        when_iso = when.isoformat(timespec="seconds")

        if mode == "old":
            # ensure list
            if not isinstance(self._raw, list):
                self._raw = []
            # patient-level conflict on same minute
            when_key = when.isoformat(timespec="minutes")
            for a in self._raw:
                if not isinstance(a, dict):
                    continue
                if a.get("patient_id") == patient_id:
                    dt = self._parse_dt(a.get("dt"))
                    if dt and dt.isoformat(timespec="minutes") == when_key:
                        return False, "You already have an appointment at that time."

            self._raw.append({
                "id": appt_id,
                "patient_id": patient_id,
                "dt": when_iso,
                "note": note or "",
            })
            self._save()
            pretty = when.strftime("%a, %d %b %Y at %I:%M %p").lstrip("0")
            return True, f"{appt_id} • {pretty}"

        # mode == "new"
        row = self._find_patient_row(patient_id)
        if not row:
            # In strict mode, we don't auto-create the patient container because you
            # curate this file. Return a helpful message.
            return False, f"Patient '{patient_id}' not found in data/appointments.json."

        # ensure container list
        if not isinstance(row.get("appointments"), list):
            row["appointments"] = []

        # conflict on same minute within this patient's appointments
        when_key = when.isoformat(timespec="minutes")
        for a in row["appointments"]:
            dt = self._parse_dt(a.get("dt"))
            if dt and dt.isoformat(timespec="minutes") == when_key:
                return False, "You already have an appointment at that time."

        row["appointments"].append({
            "id": appt_id,
            "dt": when_iso,
            "note": note or "",
        })
        row["updated_at"] = datetime.utcnow().isoformat()

        self._save()
        pretty = when.strftime("%a, %d %b %Y at %I:%M %p").lstrip("0")
        return True, f"{appt_id} • {pretty}"
