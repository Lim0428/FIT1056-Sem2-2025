from typing import Optional
from counselor_name_app.repository import Repo

class ConsentService:
    def __init__(self, repo: Optional[Repo]=None):
        self.repo = repo or Repo()

    def allowed(self, counselor_id: str, patient_id: str) -> bool:
        db = self.repo.read()
        c = db.get("consent", {}).get(patient_id, {}).get(counselor_id, False)
        assigned = db.get("patients", {}).get(patient_id, {}).get("assigned_counselor") == counselor_id
        return bool(c or assigned)

    def break_glass(self, counselor_id: str, patient_id: str, reason: str) -> bool:
        db = self.repo.read()
        db.setdefault("audit", []).append({
            "event":"break_glass","counselor":counselor_id,"patient":patient_id,"reason":reason
        })
        db.setdefault("consent", {}).setdefault(patient_id, {})[counselor_id] = True
        self.repo.write(db)
        return True
