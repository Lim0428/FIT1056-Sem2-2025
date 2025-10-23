from services.storage import read_db, write_db
from datetime import datetime

class MessagingService:
    def send(self, from_patient: str, to_role: str, content: str):
        db = read_db()
        db["messages"].append({
            "from_patient": from_patient,
            "to_role": to_role,
            "content": content,
            "ts": datetime.utcnow().isoformat()
        })
        write_db(db)

    def list_by_patient(self, patient_id: str):
        db = read_db()
        return [m for m in db["messages"] if m["from_patient"] == patient_id]
