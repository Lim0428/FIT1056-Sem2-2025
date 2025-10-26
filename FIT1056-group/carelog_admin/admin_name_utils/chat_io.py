# admin_name_utils/chat_io.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# ---------- files ----------
def _find_data_dir() -> Path:
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        d = p / "data"
        if d.is_dir():
            return d
    cwd = Path.cwd().resolve()
    for p in [cwd, *cwd.parents]:
        d = p / "data"
        if d.is_dir():
            return d
    d = cwd / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _file_for_role(role: str) -> Path:
    r = (role or "").lower()
    name = {
        "doctor": "admin_doctor_chat.json",
        "nurse": "admin_nurse_chat.json",
        "staff": "admin_staff_chat.json",
        "psychological_counselor": "admin_psych_counselor_chat.json",
    }.get(r, "admin_staff_chat.json")
    return _find_data_dir() / name

# ---------- primitives ----------
def load_chat(role: str) -> List[Dict[str, Any]]:
    p = _file_for_role(role)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            # normalize id types to strings
            for m in raw:
                if isinstance(m, dict):
                    if "from_id" in m: m["from_id"] = str(m["from_id"])
                    if "to_id" in m:   m["to_id"]   = str(m["to_id"])
            return raw
    except FileNotFoundError:
        return []
    except Exception:
        return []
    return []

def save_chat(role: str, rows: List[Dict[str, Any]]) -> None:
    p = _file_for_role(role)
    p.parent.mkdir(parents=True, exist_ok=True)
    # ensure strings for ids
    norm = []
    for m in rows:
        r = dict(m)
        r["from_id"] = str(r.get("from_id", ""))
        r["to_id"]   = str(r.get("to_id", ""))
        r.setdefault("ts", datetime.now().astimezone().isoformat(timespec="seconds"))
        r.setdefault("text", "")
        r.setdefault("read", False)
        norm.append(r)
    p.write_text(json.dumps(norm, ensure_ascii=False, indent=2), encoding="utf-8")

def append_message(role: str, message: Dict[str, Any]) -> None:
    rows = load_chat(role)
    m = dict(message)
    m["from_id"] = str(m.get("from_id", ""))
    m["to_id"]   = str(m.get("to_id", ""))
    m.setdefault("ts", datetime.now().astimezone().isoformat(timespec="seconds"))
    m.setdefault("text", "")
    m.setdefault("read", False)
    rows.append(m)
    save_chat(role, rows)

def unread_count_for_admin(admin_id: Any) -> int:
    """Count unread messages across all role files addressed TO this admin."""
    admin_id_s = str(admin_id)
    total = 0
    for role in ("doctor", "nurse", "staff", "psychological_counselor"):
        for m in load_chat(role):
            try:
                if str(m.get("to_id")) == admin_id_s and not m.get("read", False):
                    total += 1
            except Exception:
                continue
    return total
