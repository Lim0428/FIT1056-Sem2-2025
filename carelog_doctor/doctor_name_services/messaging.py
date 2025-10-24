from datetime import datetime
from .data_store import FILES, _read_json, _write_json
from .auth import current_doctor
def list_threads(store):
    me = current_doctor()
    threads = _read_json(FILES["messages"], [])
    return [t for t in threads if t["doctor_id"]==me["id"]]

def get_thread(store, thread_id: str):
    me = current_doctor()
    threads = _read_json(FILES["messages"], [])
    for t in threads:
        if t["id"]==thread_id and t["doctor_id"]==me["id"]:
            return t
    return None

def _next_thread_id(threads):
    return f"t{len(threads)+1}"

def add_message(store, thread_id: str, sender_role: str, text: str) -> bool:
    """Append a message to a thread and bump updated_at. Returns True on success."""
    threads = _read_json(FILES["messages"], [])
    now = datetime.now().isoformat()

    found = False
    for t in threads:
        if t.get("id") == thread_id:
            # optional: enforce doctor ownership
            me = current_doctor()
            if t.get("doctor_id") and t["doctor_id"] != me.get("id"):
                return False  # not this doctor's thread

            t.setdefault("messages", []).append({
                "sender_role": sender_role,
                "text": text,
                "timestamp": now,
            })
            t["updated_at"] = now
            found = True
            break

    if not found:
        return False

    _write_json(FILES["messages"], threads)
    store.audit("message.send", target=thread_id, extra={"sender": sender_role})
    return True


def mark_resolved(store, thread_id: str):
    threads = _read_json(FILES["messages"], [])
    for t in threads:
        if t["id"] == thread_id:
            t["status"] = "resolved"
            t["updated_at"] = datetime.now().isoformat()
            _write_json(FILES["messages"], threads)
            store.audit("message.resolve", target=thread_id)
            return True
    return False

# helper for seeding / creating demo thread
def seed_thread_for_patient(store, patient_id: str):
    threads = _read_json(FILES["messages"], [])
    me = current_doctor()
    tid = _next_thread_id(threads)
    threads.append({
        "id": tid,
        "doctor_id": me["id"],
        "patient_id": patient_id,
        "status": "open",
        "updated_at": datetime.now().isoformat(),
        "messages": [
            {"sender_role":"patient","text":"Hello doctor, about my medication timing…","timestamp":datetime.now().isoformat()}
        ]
    })
    _write_json(FILES["messages"], threads)
    store.audit("message.thread.create", target=tid)
    return tid
