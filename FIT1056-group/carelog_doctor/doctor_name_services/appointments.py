from datetime import datetime
from .data_store import FILES, _read_json, _write_json
from .auth import current_doctor

def list_my_appointments(store):
    me = current_doctor()
    appts = _read_json(FILES["appointments"], [])
    rows = [a for a in appts if a["doctor_id"]==me["id"]]
    rows.sort(key=lambda x: x["start"])
    return rows

def _overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end

def create_or_move_appointment(store, patient_id: str, start: datetime, end: datetime, reason: str):
    if end <= start:
        return False, "End must be after start."
    me = current_doctor()
    appts = _read_json(FILES["appointments"], [])
    for a in appts:
        if a["doctor_id"] == me["id"]:
            if _overlaps(start.isoformat(), end.isoformat(), a["start"], a["end"]):
                return False, "Double-booking prevented."
    appt_id = f"a{len(appts)+1}"
    appts.append({
        "id": appt_id,
        "doctor_id": me["id"],
        "patient_id": patient_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "reason": reason
    })
    _write_json(FILES["appointments"], appts)
    store.audit("appointment.save", target=appt_id)
    return True, appt_id

def cancel_appointment(store, appt_id: str):
    appts = _read_json(FILES["appointments"], [])
    n = [a for a in appts if a["id"] != appt_id]
    if len(n) == len(appts):
        return False, "Appointment not found."
    _write_json(FILES["appointments"], n)
    store.audit("appointment.cancel", target=appt_id)
    return True, "Cancelled"
