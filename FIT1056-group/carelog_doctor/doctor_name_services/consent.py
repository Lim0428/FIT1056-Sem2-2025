from .auth import current_doctor
from .data_store import FILES, _read_json

def ensure_doctor_can_view_patient(store, patient_id: str) -> bool:
    me = current_doctor()
    patients = _read_json(FILES["patients"], [])
    for p in patients:
        if p["id"] == patient_id:
            return (me["id"] in p.get("assigned_doctor_ids", [])) or p.get("consent_to_all_doctors", False)
    return False
