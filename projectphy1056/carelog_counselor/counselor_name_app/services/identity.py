from typing import Optional
from counselor_name_app.repository import Repo

class IdentityService:
    def __init__(self, repo: Optional[Repo]=None):
        self.repo = repo or Repo()

    def login(self, ident: str, password: str) -> Optional[dict]:
        db = self.repo.read()
        u = db.get("users", {}).get(ident)
        if not u: return None
        if u.get("locked"): return None
        if password == u.get("password"):
            u["failed"] = 0
            self.repo.write(db)
            return u
        u["failed"] = u.get("failed",0) + 1
        if u["failed"] >= 3:
            u["locked"] = True
        self.repo.write(db)
        return None

    def reset_lock(self, ident: str):
        db = self.repo.read()
        u = db.get("users", {}).get(ident)
        if not u: return
        u["failed"] = 0; u["locked"] = False
        self.repo.write(db)
