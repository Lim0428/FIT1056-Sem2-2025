from app.storage import read_db, write_db
from datetime import datetime
from typing import Dict, List, Any

class PatientService:
    def get(self, patient_id: str) -> Dict[str, Any]:
        db = read_db()
        return db["patients"].get(patient_id, {})

    def update_profile(self, patient_id: str, patch: dict) -> bool:
        db = read_db()
        p = db["patients"].get(patient_id)
        if not p:
            return False
        p.update(patch or {})
        write_db(db)
        return True

    # Surveys
    def add_survey(self, patient_id: str, survey: dict) -> None:
        db = read_db()
        db["surveys"].setdefault(patient_id, [])
        survey = dict(survey)
        survey["ts"] = survey.get("ts") or datetime.utcnow().isoformat()
        db["surveys"][patient_id].append(survey)
        write_db(db)

    def get_surveys(self, patient_id: str) -> List[dict]:
        db = read_db()
        return db["surveys"].get(patient_id, [])

    # Feedback
    def add_feedback(self, patient_id: str, feedback: dict) -> None:
        db = read_db()
        db["feedback"].setdefault(patient_id, [])
        fb = dict(feedback)
        fb["ts"] = fb.get("ts") or datetime.utcnow().isoformat()
        db["feedback"][patient_id].append(fb)
        write_db(db)

    def get_feedback(self, patient_id: str) -> List[dict]:
        db = read_db()
        return db["feedback"].get(patient_id, [])
