# admin_name_core/scheduling.py
from datetime import datetime
from typing import List, Dict

def _overlap(a_start, a_end, b_start, b_end) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)

def has_conflict(appointments: List[Dict], doctor_id: int, start_iso: str, end_iso: str, exclude_id=None) -> bool:
    s = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    e = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    for ap in appointments:
        if ap["doctor_id"] != doctor_id:
            continue
        if exclude_id and ap["id"] == exclude_id:
            continue
        if ap["status"] == "cancelled":
            continue
        ss = datetime.fromisoformat(ap["start_iso"].replace("Z", "+00:00"))
        ee = datetime.fromisoformat(ap["end_iso"].replace("Z", "+00:00"))
        if _overlap(s, e, ss, ee):
            return True
    return False
