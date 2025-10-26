# app/emergency.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone
from app.storage import read_db, write_db

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class EmergencyService:
    """
    Stores calls in FIT1056-GROUP/data/emergency.json as a list of dicts.

    Schema per record:
    {
      "id": "EC000001",
      "patient_id": "P000001",
      "patient_name": "Lim Jia Ler",
      "room": "Room A",
      "priority": "high",
      "category": "emergency",
      "note": "Auto SOS",
      "location": "Room A",      # duplicated for compatibility
      "status": "open",
      "assigned_to": "",
      "ts": "...",
      "updates": []
    }
    """

    def _load(self) -> Dict[str, Any]:
        db = read_db()
        calls = db.get("emergency")
        if not isinstance(calls, list):
            calls = []
        self._db = db
        self._calls = calls
        return db

    def _save(self) -> None:
        self._db["emergency"] = self._calls
        write_db(self._db)

    def _next_id(self, db: Dict[str, Any]) -> str:
        seq = db.get("seq") or {}
        n = int(seq.get("emg", 1))
        cid = f"EC{n:06d}"
        seq["emg"] = n + 1
        db["seq"] = seq
        return cid

    # -------- API --------
    def raise_call(
        self,
        patient_id: str,
        *,
        patient_name: str = "",
        room: str = "",
        priority: str = "high",
        category: str = "emergency",
        note: str = "Auto SOS",
    ) -> Tuple[bool, str]:
        """
        Create an emergency call immediately. Returns (ok, id or error message).
        """
        db = self._load()
        cid = self._next_id(db)
        call = {
            "id": cid,
            "patient_id": patient_id,
            "patient_name": patient_name or "",
            "room": room or "",
            "priority": (priority or "high").lower(),
            "category": (category or "emergency").lower(),
            "note": note or "Auto SOS",
            # keep a 'location' key too so other tools can read it
            "location": room or "",
            "status": "open",
            "assigned_to": "",
            "ts": _now_iso(),
            "updates": [],
        }
        self._calls.append(call)
        self._save()
        return True, cid

    def list_by_patient(self, patient_id: str) -> List[dict]:
        self._load()
        items = [c for c in self._calls if isinstance(c, dict) and c.get("patient_id") == patient_id]
        items.sort(key=lambda x: x.get("ts",""), reverse=True)
        return items

    def update_status(self, call_id: str, status: str, by: str | None = None) -> bool:
        self._load()
        for c in self._calls:
            if c.get("id") == call_id:
                c["status"] = (status or "").lower() or "open"
                c.setdefault("updates", []).append({"ts": _now_iso(), "status": c["status"], "by": by or ""})
                self._save()
                return True
        return False

    def assign(self, call_id: str, nurse_id: str) -> bool:
        self._load()
        for c in self._calls:
            if c.get("id") == call_id:
                c["assigned_to"] = nurse_id or ""
                c.setdefault("updates", []).append({"ts": _now_iso(), "status": "assigned", "by": nurse_id or ""})
                self._save()
                return True
        return False
