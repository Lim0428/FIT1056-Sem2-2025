# counselor_name_app/services/messaging.py
from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from counselor_name_app.repository import Repo

CRISIS_KEYWORDS = {"suicide","kill myself","overdose","self-harm","emergency","help now"}

class MessagingService:
    def __init__(self, repo: Optional[Repo]=None):
        self.repo = repo or Repo()

    # ---------- Directory ----------
    def get_user(self, uid: str) -> Optional[Dict]:
        return self.repo.read().get("users", {}).get(uid)

    def users_by_role(self, role: str) -> List[Dict]:
        return [u for u in self.repo.read().get("users", {}).values() if u.get("role")==role]

    def name_of(self, uid: str) -> str:
        u = self.get_user(uid)
        return u["name"] if u else uid

    # ---------- Threads ----------
    def _ensure_reads(self, t: Dict):
        t.setdefault("reads", {})
        return t

    def _last_ts(self, t: Dict) -> datetime:
        items = t.get("items", [])
        if not items: return datetime.min
        ts = items[-1]["ts"]
        return datetime.fromisoformat(ts) if isinstance(ts, str) else ts

    def list_threads(self, user_id: str, query: str = "") -> List[Dict]:
        db = self.repo.read()
        results = []
        for tid, t in db.get("messages", {}).items():
            if user_id not in t.get("members", []): 
                continue
            t = self._ensure_reads({**t, "id": tid})
            total = len(t.get("items", []))
            unread = max(0, total - int(t["reads"].get(user_id, 0)))
            title = t.get("title") or ", ".join(self.name_of(u) for u in t["members"] if u != user_id)
            last_msg = t["items"][-1]["text"] if total else ""
            if query:
                q = query.lower()
                hay = " ".join([
                    title.lower(),
                    " ".join(self.name_of(u).lower() for u in t["members"]),
                    " ".join(m["text"].lower() for m in t.get("items", []))
                ])
                if q not in hay: 
                    continue
            results.append({
                "id": tid, "title": title, "members": t["members"],
                "items": t.get("items", []), "reads": t.get("reads", {}),
                "unread": unread, "last_ts": self._last_ts(t), "last_text": last_msg
            })
        results.sort(key=lambda x: x["last_ts"], reverse=True)
        return results

    def create_or_get_thread(self, title: str, members: List[str]) -> str:
        db = self.repo.read()
        # exact same membership + same title => reuse
        for tid, t in db.get("messages", {}).items():
            if set(t.get("members", [])) == set(members) and (t.get("title") or "") == (title or ""):
                return tid
        tid = "T-" + uuid4().hex[:8]
        db.setdefault("messages", {})[tid] = {"title": title, "members": members, "items": [], "reads": {}}
        self.repo.write(db)
        return tid

    def rename_thread(self, thread_id: str, title: str):
        db = self.repo.read()
        if thread_id in db.get("messages", {}):
            db["messages"][thread_id]["title"] = title
            self.repo.write(db)

    def mark_read(self, thread_id: str, user_id: str):
        db = self.repo.read()
        t = db.get("messages", {}).get(thread_id)
        if not t: return
        total = len(t.get("items", []))
        t.setdefault("reads", {})[user_id] = total
        self.repo.write(db)

    def post(self, thread_id: Optional[str], members: List[str], sender: str, text: str, title: Optional[str]=None) -> Dict:
        db = self.repo.read()
        if not thread_id:
            thread_id = self.create_or_get_thread(title or "Conversation", members)
        t = db.setdefault("messages", {}).setdefault(thread_id, {"title": title or "Conversation", "members": members, "items": [], "reads": {}})
        item = {"by": sender, "text": text, "ts": datetime.now().isoformat(timespec="seconds")}
        t["items"].append(item)
        # crisis auto-reply + audit
        low = text.lower()
        if any(k in low for k in CRISIS_KEYWORDS):
            auto = {"by":"system",
                    "text":"If this is an emergency, please call local emergency services or go to the nearest hospital now. A staff member has been alerted.",
                    "ts": datetime.now().isoformat(timespec="seconds")}
            t["items"].append(auto)
            db.setdefault("audit", []).append({"event":"crisis_escalation","thread":thread_id})
        # Sender has read up to the end
        t.setdefault("reads", {})[sender] = len(t["items"])
        self.repo.write(db)
        return {"thread_id": thread_id}
