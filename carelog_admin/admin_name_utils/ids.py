# admin_name_utils/ids.py
from __future__ import annotations
from typing import Dict, Any
from admin_name_utils.doctors_io import list_doctors, save_doctors, upsert_doctor, delete_doctor

# Public code prefixes for each role
ROLE_PREFIX: Dict[str, str] = {
    "admin": "AD",
    "doctor": "DC",
    "nurse": "NS",
    "staff": "ST",
    "psychological_counselor": "PC",  # <- new role
}

def extract_role_number(code: str | None, prefix: str) -> int:
    """
    Return the numeric part of a code like 'DC12' given prefix 'DC'.
    If the code doesn't match, returns 0.
    """
    if not code or not prefix:
        return 0
    code = str(code).strip().upper()
    pfx = prefix.strip().upper()
    if not code.startswith(pfx):
        return 0
    tail = code[len(pfx):]
    try:
        return int(tail)
    except Exception:
        return 0

def next_role_code(db: Dict[str, Any], role: str) -> str:
    """
    Compute the next public code for the given role using ROLE_PREFIX.
    Scans db['users'] for existing codes with that prefix and increments.
    Falls back to empty string if role is unmapped.
    """
    r = (role or "").lower()
    prefix = ROLE_PREFIX.get(r)
    if not prefix:
        return ""  # unknown role; caller can handle

    users = db.get("users", []) or []
    max_num = 0
    for u in users:
        if (u.get("role") or "").lower() != r:
            continue
        code = u.get("code")
        n = extract_role_number(code, prefix)
        if n > max_num:
            max_num = n

    return f"{prefix}{max_num + 1}"

__all__ = ["ROLE_PREFIX", "next_role_code", "extract_role_number"]
