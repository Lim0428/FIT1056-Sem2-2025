from services.storage import read_db, write_db
from datetime import datetime

class AppointmentService:
    def book(self, patient_id: str, dt: datetime, note: str):
        db = read_db()
        # Simple conflict rule: same patient, same timestamp not allowed
        iso = dt.isoformat()
        for a in db["appointments"]:
            if a["patient_id"] == patient_id and a["dt"] == iso:
                return False, "You already have an appointment at this time."
        new_id = f"A{db['seq']['appt']:06d}"
        db["seq"]["appt"] += 1
        db["appointments"].append({
            "id": new_id,
            "patient_id": patient_id,
            "dt": iso,
            "note": note
        })
        write_db(db)
        return True, new_id

    def list_by_patient(self, patient_id: str):
        db = read_db()
        return [a for a in db["appointments"] if a["patient_id"] == patient_id]
