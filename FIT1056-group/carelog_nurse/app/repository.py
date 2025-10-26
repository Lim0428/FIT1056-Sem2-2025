# nurse/app/repository.py
from __future__ import annotations
from pathlib import Path
import json
from typing import Any, Dict, List
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]     # repo root
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "carelog_nurse.json"

BOOTSTRAP = {
    "meta": {"created_at": None, "updated_at": None, "version": 1},
    "nurses": [{"id": "nurse_001", "name": "Sarah Lim"}],
    "patients": [
        {"id": "p001", "name": "Nicole Tan", "gender": "F", "dob": "1960-01-10",
         "allergies": ["Penicillin"], "assigned_to": "nurse_001"},
        {"id": "p002", "name": "Alex Rivers", "gender": "M", "dob": "1989-06-21",
         "allergies": [], "assigned_to": "nurse_001"},
    ],
    "vitals": [],        # {id, patient_id, taken_at, bp, hr, temp, spo2, pain, note, author_id}
    "notes": [],         # {id, patient_id, created_at, text, author_id}
    "mar": [],           # {id, patient_id, drug, dose, route, time, author_id}
    "tasks": [           # {id, title, due_at, priority, patient_id?, status, assignee_id}
        {"id": "t001", "title": "Morning meds for p001", "due_at": "2025-10-26T08:30:00",
         "priority": "high", "patient_id": "p001", "status": "pending", "assignee_id": "nurse_001"}
    ],
    "notifications": [   # {id, created_at, type, text, patient_id?, status}
        {"id": "n001", "created_at": "2025-10-26T07:55:00", "type": "order_update",
         "text": "Dr Wong updated orders for p001", "patient_id": "p001", "status": "unread"}
    ],
    "messages": [],      # {id, created_at, from, to_role, to_id, text, patient_id?, status}
    "appointments": [],  # {id, patient_id, clinician_id, clinician_role, start, end, status, note}
}

def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()

class Repo:
    def __init__(self, path: Path = DB_PATH):
        self.path = path
        if not self.path.exists():
            data = BOOTSTRAP.copy()
            data["meta"]["created_at"] = _now_iso()
            data["meta"]["updated_at"] = data["meta"]["created_at"]
            self._write(data)

    def _read(self) -> Dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: Dict[str, Any]) -> None:
        data["meta"]["updated_at"] = _now_iso()
        tmp = self.path.with_suffix(".tmp.json")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(self.path)

    # public helpers
    def db(self) -> Dict[str, Any]: return self._read()
    def save(self, data: Dict[str, Any]) -> None: self._write(data)
    def list(self, key: str) -> List[Dict[str, Any]]: return list(self._read().get(key, []))

    def upsert(self, key: str, row: Dict[str, Any], *, id_field: str = "id") -> Dict[str, Any]:
        data = self._read()
        rows = data.setdefault(key, [])
        for i, r in enumerate(rows):
            if r.get(id_field) == row.get(id_field):
                rows[i] = row
                self._write(data)
                return row
        rows.append(row)
        self._write(data)
        return row

    def delete(self, key: str, id_value: str, *, id_field: str = "id") -> bool:
        data = self._read()
        rows = data.get(key, [])
        new_rows = [r for r in rows if r.get(id_field) != id_value]
        if len(new_rows) != len(rows):
            data[key] = new_rows
            self._write(data)
            return True
        return False

    def next_id(self, prefix: str, key: str) -> str:
        rows = self.list(key)
        nums = []
        for r in rows:
            sid = str(r.get("id", ""))
            if sid.startswith(prefix):
                try: nums.append(int(sid.replace(prefix, "")))
                except: pass
        n = (max(nums) + 1) if nums else 1
        return f"{prefix}{n:04d}"
