# app/auth.py
import hashlib
from datetime import datetime
from typing import Dict, Any, List
from app.storage import read_db, write_db


class LoginError(Exception): ...
class RegisterError(Exception): ...


def _sha256(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def _norm_identifier(x: str) -> str:
    return (x or "").strip().lower()


class AuthService:
    # -------------------------- internal helpers --------------------------
    def _record_login_event(self, user: Dict[str, Any], status: str, meta: Dict[str, Any] | None = None) -> None:
        """Append a login event to the user's login_history and clamp the list size."""
        lh: List[Dict[str, Any]] = user.setdefault("login_history", [])
        lh.append({
            "ts": datetime.utcnow().isoformat(),
            "status": status,
            "meta": meta or {},
        })
        # keep last 500 to avoid unbounded growth
        if len(lh) > 500:
            del lh[:-500]

    # ------------------------------- login --------------------------------
    def login(self, identifier: str, password: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
        db = read_db()
        ident = _norm_identifier(identifier)
        pwdh = _sha256(password)

        users = db.get("users") or {}
        for uid, u in users.items():
            if _norm_identifier(u.get("identifier", "")) == ident:
                if u.get("locked"):
                    raise LoginError("Account is locked.")
                if u.get("pwd_hash") == pwdh:
                    u["failed"] = 0
                    self._record_login_event(u, "success", meta)
                    users[uid] = u
                    db["users"] = users
                    write_db(db)
                    return u
                else:
                    u["failed"] = int(u.get("failed", 0)) + 1
                    self._record_login_event(u, "fail", meta)
                    if u["failed"] >= 5:
                        u["locked"] = True
                    users[uid] = u
                    db["users"] = users
                    write_db(db)
                    raise LoginError("Invalid credentials.")
        raise LoginError("Invalid credentials.")

    # ----------------------------- register -------------------------------
    def register_patient(
        self,
        identifier: str,
        password: str,
        security_q: str,
        security_a: str,
        profile: Dict[str, Any] | None = None,
    ) -> str:
        db = read_db()
        users = db.get("users") or {}
        patients = db.get("patients") or {}

        ident = _norm_identifier(identifier)
        if not ident or not password:
            raise RegisterError("Identifier and password are required.")

        # uniqueness
        for u in users.values():
            if _norm_identifier(u.get("identifier", "")) == ident:
                raise RegisterError("An account with this identifier already exists.")

        # allocate new patient id
        seq = db.get("seq") or {}
        next_user = int(seq.get("user", 1))
        pid = f"P{next_user:06d}"
        seq["user"] = next_user + 1
        db["seq"] = seq

        # create account (saved to data/users.json)
        users[pid] = {
            "id": pid,
            "role": "patient",
            "identifier": ident,
            "pwd_hash": _sha256(password),
            "sec_q": security_q or "",
            "sec_a_hash": _sha256(security_a),
            "failed": 0,
            "locked": False,
            "login_history": [],
        }
        db["users"] = users

        # create profile (saved to data/patient.json)
        prof = {
            "id": pid,
            "name": (profile or {}).get("name", ""),
            "dob": (profile or {}).get("dob", ""),
            "gender": (profile or {}).get("gender", ""),
            "medical_details": "",
            "emergency_contact": "",
            "pref_food": "",
            "pref_language": "",
            "pref_nurse_gender": "",
            "visible_to_non_primary": False,
            "avatar_path": "",
        }
        patients[pid] = prof
        db["patients"] = patients

        write_db(db)
        return pid

    # --------------------------- account recovery -------------------------
    def get_security_question(self, identifier: str) -> str | None:
        ident = _norm_identifier(identifier)
        users = (read_db().get("users") or {})
        for u in users.values():
            if _norm_identifier(u.get("identifier", "")) == ident:
                return u.get("sec_q") or None
        return None

    def reset_password_with_answer(self, identifier: str, answer: str, new_password: str) -> bool:
        db = read_db()
        ident = _norm_identifier(identifier)
        users = db.get("users") or {}
        for uid, u in users.items():
            if _norm_identifier(u.get("identifier", "")) == ident:
                if u.get("sec_a_hash") == _sha256(answer):
                    u["pwd_hash"] = _sha256(new_password)
                    u["failed"] = 0
                    u["locked"] = False
                    users[uid] = u
                    db["users"] = users
                    write_db(db)
                    return True
                return False
        return False

    # ---------------------------- history API -----------------------------
    def get_login_history(self, user_id: str, limit: int | None = None) -> List[Dict[str, Any]]:
        """
        Return the user's login history (most recent first).
        Used by Dashboard and Login History pages.
        """
        users = (read_db().get("users") or {})
        u = users.get(user_id)
        if not isinstance(u, dict):
            return []
        hist = list(u.get("login_history") or [])
        # Sort by timestamp descending (string ISO sort matches chronological)
        hist.sort(key=lambda e: (e or {}).get("ts", ""), reverse=True)
        return hist[:limit] if isinstance(limit, int) and limit > 0 else hist
