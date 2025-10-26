# counselor_name_app/services/safety_plans.py
from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from counselor_name_app.repository import Repo

"""
Storage model (per patient):
safety_plans = {
  "<PATIENT_ID>": [
     {
       "id": "SP-xxxxxxx",
       "patient_id": "P0001",
       "counselor_id": "C0001",
       "version": 1,
       "created_ts": "...",
       "updated_ts": "...",
       "content": {...},           # structured plan (see forms)
       "shared": {"patient": True, "care_team": True}
     },
     {... v2 ...}
  ]
}
"""

class SafetyPlanService:
    def __init__(self, repo: Optional[Repo] = None):
        self.repo = repo or Repo()

    # ---- helpers ----
    def _plans(self, pid: str) -> List[Dict]:
        return self.repo.read().get("safety_plans", {}).get(pid, [])

    def list_versions(self, patient_id: str) -> List[Dict]:
        plans = list(self._plans(patient_id))
        plans.sort(key=lambda x: (x.get("version", 0), x.get("created_ts", "")), reverse=True)
        return plans

    def latest(self, patient_id: str) -> Optional[Dict]:
        versions = self.list_versions(patient_id)
        return versions[0] if versions else None

    # ---- CRUD ----
    def create(self, patient_id: str, counselor_id: str, content: Dict,
               shared_patient: bool = True, shared_care_team: bool = True) -> Dict:
        db = self.repo.read()
        entry = {
            "id": "SP-" + uuid4().hex[:8],
            "patient_id": patient_id,
            "counselor_id": counselor_id,
            "version": 1,
            "created_ts": datetime.now().isoformat(timespec="seconds"),
            "updated_ts": datetime.now().isoformat(timespec="seconds"),
            "content": content,
            "shared": {"patient": bool(shared_patient), "care_team": bool(shared_care_team)},
        }
        db.setdefault("safety_plans", {}).setdefault(patient_id, []).append(entry)
        db.setdefault("audit", []).append({
            "event": "safety_plan_create", "patient": patient_id, "by": counselor_id, "sp": entry["id"]
        })
        self.repo.write(db)
        return entry

    def update_new_version(self, patient_id: str, counselor_id: str, base_id: str, content: Dict,
                           keep_sharing: bool = True,
                           shared_patient: Optional[bool] = None,
                           shared_care_team: Optional[bool] = None) -> Dict:
        db = self.repo.read()
        lst = db.setdefault("safety_plans", {}).setdefault(patient_id, [])
        # find base
        base = next((p for p in lst if p["id"] == base_id), None)
        share = dict(base.get("shared", {"patient": True, "care_team": True})) if (base and keep_sharing) else {
            "patient": bool(shared_patient) if shared_patient is not None else True,
            "care_team": bool(shared_care_team) if shared_care_team is not None else True
        }
        new_entry = {
            "id": "SP-" + uuid4().hex[:8],
            "patient_id": patient_id,
            "counselor_id": counselor_id,
            "version": int((lst[0]["version"] if lst else 0)) + 1,
            "created_ts": datetime.now().isoformat(timespec="seconds"),
            "updated_ts": datetime.now().isoformat(timespec="seconds"),
            "content": content,
            "shared": share,
        }
        lst.append(new_entry)
        db.setdefault("audit", []).append({
            "event": "safety_plan_update", "patient": patient_id, "by": counselor_id,
            "from": base_id, "to": new_entry["id"]
        })
        self.repo.write(db)
        return new_entry

    def delete(self, patient_id: str, plan_id: str) -> bool:
        db = self.repo.read()
        lst = db.get("safety_plans", {}).get(patient_id, [])
        before = len(lst)
        lst[:] = [p for p in lst if p["id"] != plan_id]
        if len(lst) != before:
            db.setdefault("audit", []).append({"event": "safety_plan_delete", "patient": patient_id, "sp": plan_id})
            self.repo.write(db)
            return True
        return False

    def set_sharing(self, patient_id: str, plan_id: str, patient: Optional[bool] = None, care_team: Optional[bool] = None):
        db = self.repo.read()
        lst = db.get("safety_plans", {}).get(patient_id, [])
        sp = next((p for p in lst if p["id"] == plan_id), None)
        if not sp: return
        if patient is not None:
            sp.setdefault("shared", {})["patient"] = bool(patient)
        if care_team is not None:
            sp.setdefault("shared", {})["care_team"] = bool(care_team)
        sp["updated_ts"] = datetime.now().isoformat(timespec="seconds")
        self.repo.write(db)
