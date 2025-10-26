import json
from .data_store import FILES, _read_json, _write_json
from .auth import current_doctor

def list_encounters_for_patient(store, patient_id: str):
    encs = _read_json(FILES["encounters"], [])
    view = []
    for e in encs:
        if e["patient_id"] == patient_id:
            latest = e["versions"][-1] if e["versions"] else {}
            view.append({
                "encounter_id": e["id"],
                "created_at": e["created_at"],
                "latest": latest,
                "versions": e["versions"][:-1] if len(e["versions"])>1 else []
            })
    view.sort(key=lambda x: x["created_at"], reverse=True)
    return view

def _next_encounter_id(encs):
    return f"enc{len(encs)+1}"

def add_encounter_version(store, patient_id: str, payload: dict):
    encs = _read_json(FILES["encounters"], [])
    me = current_doctor()
    bucket = None
    for e in encs:
        if e["patient_id"] == patient_id:
            bucket = e
            break
    if not bucket:
        bucket = {"id": _next_encounter_id(encs), "patient_id": patient_id, "created_at": payload["timestamp"], "versions": []}
        encs.append(bucket)
    payload = dict(payload)
    payload["author_id"] = me["id"]
    bucket["versions"].append(payload)
    _write_json(FILES["encounters"], encs)
    store.audit("encounter.save", target=patient_id)

def upload_attachment(store, patient_id: str, file):
    path = store.save_upload(patient_id, file.name, file.getbuffer())
    return path

def list_attachments(store, patient_id: str):
    p = store.list_assigned_or_consented_patients()
    # need full record
    pts = _read_json(FILES["patients"], [])
    for x in pts:
        if x["id"] == patient_id:
            return x.get("uploads", [])
    return []