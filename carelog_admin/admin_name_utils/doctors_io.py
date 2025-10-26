# carelog_admin/admin_name_utils/doctors_io.py
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any
# examples
from admin_name_utils.patients_io import list_patients, get_patient

# Project structure:
#   Project1056/
#     carelog_admin/
#       admin_name_utils/  (this file)
#     data/
#       doctors.json       (target file)
#
# doctor_management.py lives in carelog_admin/admin_name_ui/, which is a sibling of admin_name_utils/.
# The "data" folder is a sibling of carelog_admin. So from THIS file, data is two levels up.
ROOT = Path(__file__).resolve().parents[2]
DOCTORS_JSON = ROOT / "data" / "doctors.json"

def _read_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        # some people accidentally store dict; accept {"id": {...}, ...}
        if isinstance(data, dict):
            return list(data.values())
        return []
    except Exception:
        return []

def _write_json_atomic(path: Path, data: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

def _ui_from_json(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map file schema -> UI schema. We keep your UI keys and preserve unknown fields separately.
    File fields you showed:
      id, email, password, name, specialty, qualifications, license_no, working_hours,
      contact, bio, safety_q, safety_a, avatar
    UI typically uses: id, email, name, specialization, qualifications, license_no, working_hours,
                       contact, bio, avatar (and maybe others).
    """
    return {
        "id": raw.get("id"),
        "email": raw.get("email", ""),
        "name": raw.get("name", ""),
        "specialization": raw.get("specialty", ""),   # <-- map specialty -> specialization for UI
        "qualifications": raw.get("qualifications", ""),
        "license_no": raw.get("license_no", ""),
        "working_hours": raw.get("working_hours", ""),
        "contact": raw.get("contact", ""),
        "bio": raw.get("bio", ""),
        "avatar": raw.get("avatar"),
        # keep a copy of ORIGINAL dict so we can preserve unknown fields (password, safety_q, etc.)
        "_raw": raw,
    }

def _json_from_ui(ui: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map UI schema back to file schema, preserving anything we don't edit (password, safety_q, safety_a, etc.)
    """
    base = dict(ui.get("_raw", {}))  # start from original JSON row if present
    base["id"] = ui.get("id")
    base["email"] = ui.get("email", "")
    base["name"] = ui.get("name", "")
    base["specialty"] = ui.get("specialization", "")          # <-- map back to specialty
    base["qualifications"] = ui.get("qualifications", "")
    base["license_no"] = ui.get("license_no", "")
    base["working_hours"] = ui.get("working_hours", "")
    base["contact"] = ui.get("contact", "")
    base["bio"] = ui.get("bio", "")
    base["avatar"] = ui.get("avatar")
    # untouched fields (e.g., 'password', 'safety_q', 'safety_a') remain if present in _raw
    return base

# ---------------- Public API ----------------

def list_doctors() -> List[Dict[str, Any]]:
    """Return doctors as your UI expects (specialization instead of specialty)."""
    rows = _read_json_list(DOCTORS_JSON)
    return [_ui_from_json(r) for r in rows]

def save_doctors(ui_rows: List[Dict[str, Any]]) -> None:
    """
    Persist the full list back to data/doctors.json, preserving unknown fields.
    ui_rows should be the same objects you got from list_doctors() (so they still carry "_raw").
    """
    # Build an index of original rows by id to preserve their unknown fields even if UI replaced the objects.
    original = {r.get("id"): r for r in _read_json_list(DOCTORS_JSON)}
    out = []
    for u in ui_rows:
        # If the UI created a brand new dict (no _raw), we insert original by id if available
        if "_raw" not in u:
            maybe_raw = original.get(u.get("id"), {})
            u = dict(u)
            u["_raw"] = maybe_raw
        out.append(_json_from_ui(u))
    _write_json_atomic(DOCTORS_JSON, out)

def upsert_doctor(ui_row: Dict[str, Any]) -> None:
    """Insert or update one doctor by id."""
    docs = list_doctors()
    ids = [d.get("id") for d in docs]
    if ui_row.get("id") in ids:
        docs = [ui_row if d.get("id") == ui_row.get("id") else d for d in docs]
    else:
        docs.append(ui_row)
    save_doctors(docs)

def delete_doctor(doc_id: str) -> bool:
    """Delete a doctor by id; return True if deleted."""
    docs = list_doctors()
    new_docs = [d for d in docs if d.get("id") != doc_id]
    if len(new_docs) == len(docs):
        return False
    save_doctors(new_docs)
    return True
