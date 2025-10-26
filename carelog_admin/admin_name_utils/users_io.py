# admin_name_utils/users_io.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import json

# ---------- locate <project>/data reliably ----------
def _find_data_dir() -> Path:
    """
    Walk up from this file and from the CWD to find a folder literally named 'data'.
    Works whether you run 'streamlit run admin_name_app.py' from project root
    or from inside carelog_admin/.
    """
    # First, walk up from this file
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        dd = p / "data"
        if dd.is_dir():
            return dd

    # Fallback: walk up from current working directory (safer for IDE runs)
    cwd = Path.cwd().resolve()
    for p in [cwd, *cwd.parents]:
        dd = p / "data"
        if dd.is_dir():
            return dd

    # Last resort: create ./data next to CWD
    dd = cwd / "data"
    dd.mkdir(parents=True, exist_ok=True)
    return dd

def admin_users_path() -> Path:
    return _find_data_dir() / "admin_users.json"

# ---------- load/save ----------
_EXPECTED_ROLES = {"doctor", "nurse", "staff", "psychological_counselor"}

def _norm_user(u: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Normalize a user row from admin_users.json.
    Only returns non-admin roles — these are the peers the admin can chat with.
    """
    if not isinstance(u, dict):
        return None

    rid = u.get("id")
    # IDs can be str or int; keep as-is for chat but ensure not None
    if rid is None:
        return None

    role = str(u.get("role", "")).strip().lower()
    if role not in _EXPECTED_ROLES:
        return None  # ignore admins or unknown roles

    return {
        "id": rid,
        "name": u.get("name", "User"),
        "email": u.get("email", ""),
        "role": role,
        "locked": bool(u.get("locked", False)),
    }

def load_admin_side_users() -> List[Dict[str, Any]]:
    """
    Read data/admin_users.json and return a clean list of non-admin users
    (doctors, nurses, staff, psychological_counselor).
    """
    path = admin_users_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except Exception:
        return []

    out: List[Dict[str, Any]] = []
    if isinstance(raw, list):
        for row in raw:
            nr = _norm_user(row)
            if nr:
                out.append(nr)
    return out

def save_admin_side_users(users: List[Dict[str, Any]]) -> None:
    """
    Utility: write normalized users back to admin_users.json (optional).
    """
    path = admin_users_path()
    # Persist only expected keys
    payload = []
    for u in users:
        nr = _norm_user(u)
        if nr:
            payload.append({
                "id": nr["id"],
                "name": nr["name"],
                "email": nr["email"],
                "role": nr["role"],
                "locked": bool(nr.get("locked", False)),
            })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
