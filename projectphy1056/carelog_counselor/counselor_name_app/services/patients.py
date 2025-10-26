from typing import List, Dict, Optional
from counselor_name_app.repository import Repo

class PatientService:
    def __init__(self, repo: Optional[Repo]=None):
        self.repo = repo or Repo()

    def list_assigned(self, counselor_id: str) -> List[Dict]:
        db = self.repo.read()
        return [p for p in db.get("patients", {}).values()
                if p.get("assigned_counselor") == counselor_id]

    def get(self, pid: str) -> Optional[Dict]:
        return self.repo.read().get("patients", {}).get(pid)
