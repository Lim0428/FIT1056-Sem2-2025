from services.storage import read_db, write_db
from datetime import datetime
import hashlib
from typing import Optional, Dict

def _hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

class LoginError(Exception):
    pass

class AuthService:
    LOCKOUT_THRESHOLD = 3

    def register_patient(self, identifier: str, password: str, security_q: str, security_a: str, profile: Dict) -> str:
        db = read_db()
        # uniqueness by identifier
        for u in db["users"].values():
            if u["identifier"].lower() == identifier.lower():
                raise ValueError("Account already exists.")
        uid = f"P{db['seq']['user']:06d}"
        db["seq"]["user"] += 1
        db["users"][uid] = {
            "id": uid,
            "role": "patient",
            "identifier": identifier,
            "pwd_hash": _hash(password),
            "sec_q": security_q,
            "sec_a_hash": _hash(security_a),
            "failed": 0,
            "locked": False,
            "login_history": []
        }
        # bare patient profile
        db["patients"][uid] = {
            "id": uid,
            "name": profile.get("name",""),
            "dob": profile.get("dob",""),
            "gender": "",
            "medical_details": "",
            "emergency_contact": "",
            "pref_food": "",
            "pref_language": "",
            "pref_nurse_gender": "",
            "visible_to_non_primary": False
        }
        write_db(db)
        return uid

    def get_security_question(self, identifier: str) -> Optional[str]:
        db = read_db()
        ident = (identifier or "").lower()
        for u in db["users"].values():
            if u["identifier"].lower() == ident:
                return u.get("sec_q")
        return None

    def reset_password_with_answer(self, identifier: str, answer: str, new_password: str) -> bool:
        db = read_db()
        ident = (identifier or "").lower()
        for u in db["users"].values():
            if u["identifier"].lower() == ident:
                if _hash(answer) == u.get("sec_a_hash"):
                    u["pwd_hash"] = _hash(new_password)
                    u["failed"] = 0
                    u["locked"] = False
                    write_db(db)
                    return True
        return False

    def _record_login(self, user: Dict, status: str, meta=None):
        user["login_history"].append({
            "ts": datetime.utcnow().isoformat(),
            "status": status,
            "meta": meta or {}
        })

    def login(self, identifier: str, password: str, meta=None) -> Dict:
        db = read_db()
        user = None
        ident = (identifier or "").lower()
        for u in db["users"].values():
            if u["identifier"].lower() == ident:
                user = u
                break
        if not user:
            raise LoginError("Invalid credentials.")
        if user.get("locked"):
            self._record_login(user, "locked", meta)
            write_db(db)
            raise LoginError("Account locked after multiple failed attempts.")

        if user["pwd_hash"] != _hash(password):
            user["failed"] = user.get("failed", 0) + 1
            status = "fail"
            if user["failed"] >= self.LOCKOUT_THRESHOLD:
                user["locked"] = True
                status = "locked"
            self._record_login(user, status, meta)
            write_db(db)
            raise LoginError("Invalid credentials.")
        # success
        user["failed"] = 0
        self._record_login(user, "success", meta)
        write_db(db)
        return user

    def get_login_history(self, user_id: str):
        db = read_db()
        u = db["users"].get(user_id)
        if not u:
            return []
        return u.get("login_history", [])
