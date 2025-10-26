# medical_staff/app/staff_service.py
from __future__ import annotations
from typing import Any, Dict, List, Optional

from .staff_db import read_staff_items, write_staff_items, bump_staff_seq

def _next_staff_id(n: int) -> str:
    # S001, S002, ...
    return f"S{int(n):03d}"

class StaffService:
    """
    Service for CRUD over data/medical_staff.json
    Item shape (suggested):
      {
        "id": "S001",
        "name": "Alice Tan",
        "role": "Nurse",         # or "Doctor", "Pharmacist", ...
        "email": "alice@hosp.org",
        "phone": "+65 1234 5678",
        "active": true,
        "assigned_patients": ["P000001", "P000005"]
      }
    """

    # ---------- reads ----------
    def list(self, *, active_only: bool = False) -> List[Dict[str, Any]]:
        items = read_staff_items()
        if active_only:
            items = [s for s in items if s.get("active", True)]
        # sort by id by default
        return sorted(items, key=lambda r: r.get("id",""))

    def get(self, staff_id: str) -> Optional[Dict[str, Any]]:
        sid = (staff_id or "").strip()
        for s in read_staff_items():
            if (s.get("id") or "").strip() == sid:
                return s
        return None

    # ---------- writes ----------
    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        items = read_staff_items()
        new_id = _next_staff_id(bump_staff_seq())
        row = {
            "id": new_id,
            "name": data.get("name", "").strip(),
            "role": data.get("role", "Medical Staff"),
            "email": data.get("email", "").strip(),
            "phone": data.get("phone", "").strip(),
            "active": bool(data.get("active", True)),
            "assigned_patients": list(data.get("assigned_patients", [])),
        }
        items.append(row)
        write_staff_items(items)
        return row

    def update(self, staff_id: str, patch: Dict[str, Any]) -> bool:
        sid = (staff_id or "").strip()
        items = read_staff_items()
        ok = False
        for s in items:
            if (s.get("id") or "").strip() == sid:
                s.update({
                    k: (list(v) if k == "assigned_patients" else v)
                    for k, v in (patch or {}).items()
                    if v is not None
                })
                ok = True
                break
        if ok:
            write_staff_items(items)
        return ok

    def delete(self, staff_id: str) -> bool:
        sid = (staff_id or "").strip()
        items = read_staff_items()
        new_items = [s for s in items if (s.get("id") or "").strip() != sid]
        if len(new_items) == len(items):
            return False
        write_staff_items(new_items)
        return True
