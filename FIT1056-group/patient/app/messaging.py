# patient/app/messaging.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, List, Any
from app.storage import read_db, write_db

_DB_KEY = "messages"

def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

class MessagingService:
    def _load(self) -> Dict[str, Any]:
        db = read_db()
        if _DB_KEY not in db or not isinstance(db[_DB_KEY], list):
            db[_DB_KEY] = []
        return db

    def _save(self, db: Dict[str, Any]) -> None:
        write_db(db)

    def send(self, patient_id: str, to_role: str, content: str, *, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
        txt = (content or "").strip()
        if not txt:
            raise ValueError("content is empty")
        role = (to_role or "").strip() or "Nurse"

        db = self._load()
        items: List[Dict[str, Any]] = db[_DB_KEY]
        next_id = (items[-1]["id"] + 1) if items else 1

        item = {
            "id": next_id,
            "ts": _now_iso(),
            "from_pid": patient_id,
            "to_role": role,
            "content": txt,
            "meta": dict(meta or {}),
        }
        items.append(item)
        self._save(db)
        return item

    def list_by_patient(self, patient_id: str) -> List[Dict[str, Any]]:
        db = self._load()
        return [m for m in db[_DB_KEY] if m.get("from_pid") == patient_id]

    def list_for_role(self, role: str) -> List[Dict[str, Any]]:
        r = (role or "").strip()
        db = self._load()
        return [m for m in db[_DB_KEY] if (m.get("to_role") or "").strip() == r]
