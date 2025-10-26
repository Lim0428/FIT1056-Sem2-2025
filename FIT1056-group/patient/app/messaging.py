# app/messaging.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from datetime import datetime
from app.storage import read_db, write_db


def _utcnow() -> str:
    return datetime.utcnow().isoformat()


class MessagingService:
    """
    Threaded messaging stored in FIT1056-GROUP/data/messages.json

    Schema:
    [
      {
        "id": 1,
        "patient_id": "P000001",
        "doctor_id": "D000001",
        "status": "open",
        "updated_at": "2025-10-25T20:02:26.255835",
        "messages": [
          {"id":"m1","sender_role":"patient","text":"...","timestamp":"..."},
          {"id":"m2","sender_role":"doctor","text":"...","timestamp":"..."}
        ]
      }
    ]
    """

    # ---------- internal ----------
    def _load(self) -> Dict[str, Any]:
        db = read_db()
        msgs = db.get("messages")
        if not isinstance(msgs, list):
            msgs = []
        self._db = db
        self._threads: List[Dict[str, Any]] = msgs
        return db

    def _save(self) -> None:
        self._db["messages"] = self._threads
        write_db(self._db)

    def _next_thread_id(self) -> int:
        db = self._db
        seq = db.get("seq") or {}
        nxt = int(seq.get("msg", 1))
        # avoid collision with existing ids
        for t in self._threads:
            try:
                nxt = max(nxt, int(t.get("id", 0)) + 1)
            except Exception:
                pass
        seq["msg"] = nxt + 1
        db["seq"] = seq
        return nxt

    def _next_message_id(self, thread: Dict[str, Any]) -> str:
        n = 1
        for m in (thread.get("messages") or []):
            mid = str(m.get("id", "")).lower().lstrip("m")
            try:
                n = max(n, int(mid) + 1)
            except Exception:
                pass
        return f"m{n}"

    # ---------- threaded API ----------
    def list_threads_by_patient(self, patient_id: str) -> List[Dict[str, Any]]:
        self._load()
        threads = [t for t in self._threads if isinstance(t, dict) and t.get("patient_id") == patient_id]
        threads.sort(key=lambda t: t.get("updated_at", ""), reverse=True)
        return threads

    def get_thread(self, thread_id: int) -> Dict[str, Any] | None:
        self._load()
        for t in self._threads:
            if t.get("id") == thread_id:
                return t
        return None

    def open_thread(self, patient_id: str, doctor_id: str | None = None) -> int:
        self._load()
        tid = self._next_thread_id()
        self._threads.append({
            "id": tid,
            "patient_id": patient_id,
            "doctor_id": doctor_id or "",
            "status": "open",
            "updated_at": _utcnow(),
            "messages": [],
        })
        self._save()
        return tid

    def send_patient_message(
        self,
        patient_id: str,
        text: str,
        doctor_id: str | None = None,
        thread_id: int | None = None,
    ) -> Tuple[bool, str | int]:
        if not (text or "").strip():
            return False, "Message cannot be empty."

        self._load()

        # find/reuse thread
        thread = None
        if isinstance(thread_id, int):
            thread = self.get_thread(thread_id)
        if thread is None:
            cands = [
                t for t in self._threads
                if t.get("patient_id") == patient_id and t.get("status") == "open"
                   and (doctor_id is None or t.get("doctor_id") == doctor_id)
            ]
            cands.sort(key=lambda t: t.get("updated_at", ""), reverse=True)
            thread = cands[0] if cands else None
        if thread is None:
            tid = self.open_thread(patient_id, doctor_id)
            thread = self.get_thread(tid)

        msg = {
            "id": self._next_message_id(thread),
            "sender_role": "patient",
            "text": text.strip(),
            "timestamp": _utcnow(),
        }
        thread.setdefault("messages", []).append(msg)
        thread["updated_at"] = msg["timestamp"]
        self._save()
        return True, thread["id"]

    def send_doctor_message(self, thread_id: int, text: str) -> bool:
        if not (text or "").strip():
            return False
        self._load()
        thread = self.get_thread(thread_id)
        if not thread:
            return False
        msg = {
            "id": self._next_message_id(thread),
            "sender_role": "doctor",
            "text": text.strip(),
            "timestamp": _utcnow(),
        }
        thread.setdefault("messages", []).append(msg)
        thread["updated_at"] = msg["timestamp"]
        self._save()
        return True

    def close_thread(self, thread_id: int) -> bool:
        self._load()
        t = self.get_thread(thread_id)
        if not t:
            return False
        t["status"] = "closed"
        t["updated_at"] = _utcnow()
        self._save()
        return True

    # ---------- legacy helpers ----------
    def list_by_patient(self, patient_id: str) -> List[Dict[str, Any]]:
        flat: List[Dict[str, Any]] = []
        for t in self.list_threads_by_patient(patient_id):
            for m in t.get("messages", []):
                flat.append({
                    "id": m.get("id"),
                    "from_pid": patient_id if m.get("sender_role") == "patient" else "",
                    "to_role": "Doctor" if m.get("sender_role") == "patient" else "Patient",
                    "content": m.get("text"),
                    "ts": m.get("timestamp"),
                    "_thread_id": t.get("id"),
                    "_doctor_id": t.get("doctor_id", ""),
                    "_status": t.get("status", "open"),
                })
        flat.sort(key=lambda x: x.get("ts", ""), reverse=True)
        return flat

    def add_message(self, patient_id: str, to_role: str, content: str, meta: Dict[str, Any] | None = None) -> bool:
        doctor_id = (meta or {}).get("doctor_id") if isinstance(meta, dict) else None
        ok, _ = self.send_patient_message(patient_id, content, doctor_id=doctor_id)
        return bool(ok)
