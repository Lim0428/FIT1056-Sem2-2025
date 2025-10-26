from .data_store import FILES, _read_json
from .auth import current_doctor
from .consent import ensure_doctor_can_view_patient

def patient_miniview(store, patient_id: str) -> dict:
    pts = _read_json(FILES["patients"], [])
    for p in pts:
        if p["id"] == patient_id:
            return p
    return {}

def search_patients_by_keyword(store, keyword: str):
    pts = _read_json(FILES["patients"], [])
    me = current_doctor()
    kw = keyword.lower().strip()
    rows = []
    for p in pts:
        allowed = (me["id"] in p.get("assigned_doctor_ids", [])) or p.get("consent_to_all_doctors", False)
        if not allowed:
            continue
        joined = f"{p.get('id','')} {p.get('name','')} {p.get('contact','')}".lower()
        if kw in joined:
            rows.append({"id":p["id"],"name":p["name"],"contact":p["contact"]})
    return rows