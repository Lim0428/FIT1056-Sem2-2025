from typing import Dict, List
from counselor_name_app.repository import Repo

class AuditService:
    def __init__(self, repo: Repo | None = None):
        self.repo = repo or Repo()

    def log(self, event: str, **fields):
        db = self.repo.read()
        db.setdefault("audit", []).append({"event":event, **fields})
        self.repo.write(db)

    def list(self) -> List[Dict]:
        return self.repo.read().get("audit", [])
