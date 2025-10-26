# app/patient.py
from __future__ import annotations
from app.storage import read_db, write_db, data_dir
from datetime import datetime
from typing import Dict, List, Any
import os


class PatientService:
    # ---------- Profiles ----------
    def get(self, patient_id: str) -> Dict[str, Any]:
        db = read_db()
        return (db.get("patients") or {}).get(patient_id, {})

    def update_profile(self, patient_id: str, patch: dict) -> bool:
        """
        Update a patient's profile and return True on success.
        """
        db = read_db()
        patients = db.get("patients") or {}
        p = patients.get(patient_id)
        if not isinstance(p, dict):
            return False
        p.update(patch or {})
        patients[patient_id] = p
        db["patients"] = patients
        write_db(db)
        return True

    def set_avatar(self, patient_id: str, image_bytes: bytes, filename: str | None = None) -> bool:
        """
        Save avatar to <REPO>/data/avatars/<PID>.<ext> and update patients[PID]['avatar_path'].
        Returns True when both file and JSON are updated.
        """
        if not image_bytes:
            return False

        # Ensure avatars dir
        ddir = data_dir()  # absolute path to <REPO>/data
        avatars_dir = os.path.join(ddir, "avatars")
        os.makedirs(avatars_dir, exist_ok=True)

        # Choose extension
        ext = "png"
        if filename:
            lower = filename.lower()
            if lower.endswith(".jpg") or lower.endswith(".jpeg"):
                ext = "jpg"
            elif lower.endswith(".webp"):
                ext = "webp"
            elif lower.endswith(".gif"):
                ext = "gif"

        # Save file
        avatar_abs = os.path.join(avatars_dir, f"{patient_id}.{ext}")
        with open(avatar_abs, "wb") as f:
            f.write(image_bytes)

        # Update JSON
        rel_path = f"data/avatars/{patient_id}.{ext}"
        db = read_db()
        patients = db.get("patients") or {}
        p = patients.get(patient_id, {})
        if not isinstance(p, dict):
            p = {"id": patient_id}
        p["avatar_path"] = rel_path
        patients[patient_id] = p
        db["patients"] = patients
        write_db(db)
        return True

    # ---------- Surveys (→ FIT1056-GROUP/data/surveys.json) ----------
    def add_survey(self, patient_id: str, survey: dict) -> bool:
        db = read_db()
        db.setdefault("surveys", {})
        patient_surveys = db["surveys"].setdefault(patient_id, [])
        s = {
            "mood": (survey or {}).get("mood", ""),
            "pain": int((survey or {}).get("pain", 0)),
            "sleep": float((survey or {}).get("sleep", 0)),
            "meds": bool((survey or {}).get("meds", False)),
            "note": (survey or {}).get("note", ""),
            "ts": (survey or {}).get("ts") or datetime.utcnow().isoformat(),
        }
        patient_surveys.append(s)
        write_db(db)
        return True

    def get_surveys(self, patient_id: str) -> List[dict]:
        db = read_db()
        items = (db.get("surveys") or {}).get(patient_id, [])
        try:
            return sorted(items, key=lambda x: (x or {}).get("ts", ""), reverse=True)
        except Exception:
            return items

    # ---------- Feedback ----------
    def add_feedback(self, patient_id: str, feedback: dict) -> None:
        db = read_db()
        db.setdefault("feedback", {})
        db["feedback"].setdefault(patient_id, [])
        fb = dict(feedback or {})
        fb["ts"] = fb.get("ts") or datetime.utcnow().isoformat()
        db["feedback"][patient_id].append(fb)
        write_db(db)

    def get_feedback(self, patient_id: str) -> List[dict]:
        db = read_db()
        return (db.get("feedback") or {}).get(patient_id, [])
