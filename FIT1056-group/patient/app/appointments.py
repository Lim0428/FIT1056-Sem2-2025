# app/appointments.py
from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Tuple, Any

from app.storage import read_db, write_db


class AppointmentService:
    """
    Works with BOTH schemas stored in data/appointments.json.

    Old (flat list):
      [
        {"id": "A000001", "patient_id": "P000001", "dt": "2025-10-24T11:00:00", "note": ""}
      ]

    New (patient-centric):
      [
        {
          "id": "P000001",
          "name": "Jane Doe",
          "contact": "0123-456 789",
          "appointments": [
            {"id": "A000001", "dt": "2025-10-30T12:00:00", "note": ""}
          ],
          "updated_at": "ISO-TS",
          ...
        }
      ]

    Public API (unchanged):
      - list_by_patient(patient_id) -> List[dict]
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
        return self._db

    def _save(self) -> None:
        self._db["appointments"] = self._raw
        write_db(self._db)

    def _mode(self) -> str:
        """Detect schema: 'old' (flat slot list) or 'new' (patient-centric)."""
        for item in self._raw:
            if isinstance(item, dict):
                if "patient_id" in item and "dt" in item:
                    return "old"
                if "appointments" in item or "assigned_doctor_ids" in item or "consent_to_all_doctors" in item:
                    return "new"
        # empty file: default to new
        return "new"

    def _find_patient_row(self, patient_id: str) -> Dict[str, Any] | None:
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

    # ---------- patient bootstrap for NEW schema ----------
    def _ensure_patient_row_in_new_schema(self, patient_id: str) -> Dict[str, Any]:
        """
        Ensure a patient container exists in appointments.json (NEW schema).
        If missing, read from data/patient.json (db['patients']) and create a row.
        Returns the row (existing or created). If no patient info found at all,
        returns an empty dict.
        """
        row = self._find_patient_row(patient_id)
        if row:
            return row

        # Pull basic info from the patient registry (data/patient.json)
        db = self._db if hasattr(self, "_db") else read_db()
        patients = db.get("patients") or []
        found = None
        for p in patients:
            if isinstance(p, dict) and p.get("id") == patient_id:
                found = p
                break

        if not found:
            # We allow creation even if patients.json doesn't have a record;
            # we just make a minimal container so booking still works.
            found = {"id": patient_id, "name": "", "contact": ""}

        # Create a new container row inside appointments.json
        row = {
            "id": found.get("id", patient_id),
            "name": found.get("name", ""),
            "contact": found.get("emergency_contact", "") or found.get("contact", ""),
            "appointments": [],
            "updated_at": datetime.utcnow().isoformat(),
        }
        # Make sure the top-level list exists
        if not isinstance(self._raw, list):
            self._raw = []
        self._raw.append(row)
        self._save()  # persist the new container immediately
        return row

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
        NEW schema: ensure a patient row exists (created from data/patient.json
                    if necessary), then append.
        OLD schema: append to the top-level list.
        """
        if not isinstance(when, datetime):
            return False, "Invalid time."

        db = self._load()
        mode = self._mode()

        now = datetime.now()
        if when < now.replace(second=0, microsecond=0):
            return False, "Cannot book a past time."

        appt_id = self._next_appt_id(db)
        when_iso = when.isoformat(timespec="seconds")
        when_key = when.isoformat(timespec="minutes")

        if mode == "old":
            if not isinstance(self._raw, list):
                self._raw = []
            # conflict for THIS patient on same minute
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

        # mode == "new"  → ensure patient row exists (create from patients.json if missing)
        row = self._ensure_patient_row_in_new_schema(patient_id)
        if not row:
            return False, f"Unable to create patient container for '{patient_id}'."

        if not isinstance(row.get("appointments"), list):
            row["appointments"] = []

        # conflict inside this patient's appointments
        for a in row["appointments"]:
            dt = self._parse_dt(a.get("dt"))
            if dt and dt.isoformat(timespec="minutes") == when_key:
                return False, "You already have an appointment at that time."

        row["appointments"].append({"id": appt_id, "dt": when_iso, "note": note or ""})
        row["updated_at"] = datetime.utcnow().isoformat()
        self._save()

        pretty = when.strftime("%a, %d %b %Y at %I:%M %p").lstrip("0")
        return True, f"{appt_id} • {pretty}"
