# admin_name_ui/user_management.py
from __future__ import annotations

from datetime import datetime, time
from typing import List, Dict, Any
import secrets
import string
import re
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from admin_name_utils.storage import (
    load_db, save_db,
    load_admin_users, save_admin_users,   # <-- external source of truth
)
from admin_name_utils.ids import ROLE_PREFIX, next_role_code, extract_role_number  # role codes

# ---------------------------- constants ----------------------------
ROLE_OPTIONS = ["admin", "doctor", "nurse", "staff", "psychological_counselor"]
WEEK_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ---------------------------- external paths ----------------------------
def _project_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / "data").is_dir():
            return p
    return Path.cwd()

def _data_dir() -> Path:
    return _project_root() / "data"

def _doctors_file_path() -> Path:
    return _data_dir() / "doctors.json"

# ---------------------------- small helpers ----------------------------
def _role_icon(role: str) -> str:
    r = (role or "").lower()
    return {
        "admin": "🛡️",
        "doctor": "🩺",
        "nurse": "🧑‍⚕️",
        "staff": "🧑‍💼",
        "psychological_counselor": "🧠",
    }.get(r, "👤")

def _badge(text: str, tone: str = "neutral"):
    tones = {
        "neutral": "rgba(255,255,255,.12)",
        "ok": "rgba(34,197,94,.25)",
        "warn": "rgba(234,179,8,.25)",
        "err": "rgba(239,68,68,.25)",
        "info": "rgba(59,130,246,.25)",
    }
    return f"<span style='background:{tones.get(tone, tones['neutral'])};padding:4px 10px;border-radius:999px;font-size:12px;'>{text}</span>"

def _card_header(title: str, emoji: str = ""):
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:10px;">
               <div style="font-size:20px">{emoji}</div>
               <h4 style="margin:0;">{title}</h4>
           </div>""",
        unsafe_allow_html=True,
    )

def _kpi(label: str, value: str):
    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
            padding:10px 14px;border:1px solid rgba(255,255,255,.1);border-radius:14px;
            background:rgba(255,255,255,.03);">
            <div style="opacity:.9">{label}</div>
            <div style="font-weight:700">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _valid_email(s: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s or ""))

def _generate_password(length: int = 12) -> str:
    import random
    alphabet_u = string.ascii_uppercase
    alphabet_l = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*()-_=+"
    base = [
        secrets.choice(alphabet_u),
        secrets.choice(alphabet_l),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]
    pool = alphabet_u + alphabet_l + digits + symbols
    base += [secrets.choice(pool) for _ in range(max(4, length - len(base)))]
    random.SystemRandom().shuffle(base)
    return "".join(base[:length])

def _password_strength_hint(pw: str) -> str:
    score = 0
    if any(c.islower() for c in pw): score += 1
    if any(c.isupper() for c in pw): score += 1
    if any(c.isdigit() for c in pw): score += 1
    if any(c in "!@#$%^&*()-_=+" for c in pw): score += 1
    if len(pw) >= 12: score += 1
    labels = {1: "very weak", 2: "weak", 3: "fair", 4: "good", 5: "strong"}
    return labels.get(score, "very weak")

def _str_to_time(s: str, default: time) -> time:
    try:
        hh, mm = (s or "").split(":")
        return time(int(hh), int(mm))
    except Exception:
        return default

def _time_from_str(hhmm: str, fallback: time) -> time:
    try:
        hh, mm = map(int, str(hhmm).split(":"))
        return time(h, mm)
    except Exception:
        return fallback

def _time_to_str(t: time) -> str:
    return f"{t.hour:02d}:{t.minute:02d}"

def _default_availability_for_role(role: str):
    r = (role or "").lower()
    if r in ("doctor", "nurse"):
        return [{"day": d, "start": "09:00", "end": "17:00"} for d in WEEK_DAYS[:5]]
    return []

def _coerce_slots(initial):
    """Normalize availability into list[{'day','start','end'}]."""
    if not initial:
        return []
    if isinstance(initial, list):
        out = []
        for x in initial:
            if isinstance(x, dict):
                d = str(x.get("day", "")).strip().title()[:3] or "Mon"
                s = str(x.get("start", "09:00")).strip() or "09:00"
                e = str(x.get("end", "17:00")).strip() or "17:00"
                out.append({"day": d, "start": s, "end": e})
        return out
    if isinstance(initial, str):
        try:
            data = json.loads(initial)
        except Exception:
            return []
        return _coerce_slots(data)
    return []

# ---------------------------- external users merge ----------------------------
def _norm_admin_user(u: Dict[str, Any]) -> Dict[str, Any]:
    role = (u.get("role", "staff") or "staff").lower()
    if role not in ROLE_OPTIONS:
        role = "staff"
    return {
        "id": u.get("id"),
        "code": u.get("code", ""),
        "name": u.get("name", ""),
        "email": u.get("email", ""),
        "role": role,
        "locked": bool(u.get("locked", False)),
        "pwd": u.get("pwd", "changeme123"),
        "must_change_pwd": bool(u.get("must_change_pwd", True)),
        "specialization": u.get("specialization", u.get("specialty", "")),
        "qualifications": u.get("qualifications", ""),
        "availability": _coerce_slots(u.get("availability", [])),
        "note": u.get("note", ""),
        "_source": "admin_users",
    }

def _load_doctors_file() -> List[Dict[str, Any]]:
    p = _doctors_file_path()
    if not p.exists():
        return []
    try:
        arr = json.loads(p.read_text(encoding="utf-8")) or []
        if not isinstance(arr, list):
            return []
    except Exception:
        return []
    out = []
    for d in arr:
        if not isinstance(d, dict):
            continue
        out.append({
            "id": d.get("id", d.get("code", "")),
            "code": d.get("code", ""),
            "name": d.get("name", ""),
            "email": d.get("email", ""),
            "role": "doctor",
            "locked": False,
            "pwd": d.get("password", "changeme123"),
            "must_change_pwd": True,
            "specialization": d.get("specialty", d.get("specialization", "")),
            "qualifications": d.get("qualifications", ""),
            "availability": _coerce_slots(d.get("availability", [])),
            "note": d.get("bio", ""),
            "_source": "doctors_json",
        })
    return out

def _merge_users(admin_users: List[Dict[str, Any]], doctors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge by email first, then by id. Rows from admin_users win;
    we fill missing doctor metadata from doctors.json. Doctors-only rows remain read-only.
    """
    by_email: Dict[str, Dict[str, Any]] = {}
    by_id: Dict[str, Dict[str, Any]] = {}

    for u in admin_users:
        key_email = (u.get("email") or "").lower()
        if key_email:
            by_email[key_email] = u
        elif u.get("id") is not None:
            by_id[str(u["id"])] = u

    for d in doctors:
        key_email = (d.get("email") or "").lower()
        if key_email and key_email in by_email:
            base = by_email[key_email]
            # ensure doctor role and fill blanks
            base["role"] = "doctor"
            for k in ("specialization", "qualifications", "note", "code"):
                if not base.get(k) and d.get(k):
                    base[k] = d[k]
        else:
            did = str(d.get("id", ""))
            if did and did in by_id:
                base = by_id[did]
                base["role"] = "doctor"
                for k in ("specialization", "qualifications", "note", "code"):
                    if not base.get(k) and d.get(k):
                        base[k] = d[k]
            else:
                by_id[did or f"doc_{len(by_id)+1}"] = d

    merged = list({id(u): u for u in [*by_email.values(), *by_id.values()]}.values())
    return merged

def _coerce_int_id(x) -> int:
    """Turn any id into a stable int for mirroring into carelog.json."""
    try:
        return int(x)
    except Exception:
        pass
    s = str(x or "")
    h = 0
    for ch in s:
        h = (h * 131 + ord(ch)) & 0x7fffffff
    return 10000 + (h % 900000)

def _mirror_into_db(users_merged: List[Dict[str, Any]]) -> None:
    db = load_db()
    mirrored = []
    for u in users_merged:
        mid = _coerce_int_id(u.get("id"))
        mirrored.append({
            "id": mid,
            "code": u.get("code", ""),
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "role": u.get("role", "staff"),
            "locked": bool(u.get("locked", False)),
            "pwd": u.get("pwd", "changeme123"),
            "must_change_pwd": bool(u.get("must_change_pwd", True)),
            "specialization": u.get("specialization", ""),
            "qualifications": u.get("qualifications", ""),
            "availability": _coerce_slots(u.get("availability", [])),
            "note": u.get("note", ""),
        })
    db["users"] = mirrored
    save_db(db)

# ---------------------------- Delete helper ----------------------------
def _delete_user_and_cleanup_admin_users(email: str) -> str:
    """
    Remove a user from data/admin_users.json by email.
    Returns: 'ok' | 'notfound' | 'last_admin' | 'self'
    """
    db = load_db()
    me = st.session_state.get("user", {})
    me_email = (me.get("email") or "").lower()

    cur = [u for u in load_admin_users()]
    target = next((u for u in cur if (u.get("email","").lower() == (email or "").lower())), None)
    if not target:
        return "notfound"

    # prevent deleting yourself if you're the only admin
    if target.get("email","").lower() == me_email:
        return "self"
    if (target.get("role") == "admin") and sum((x.get("role") == "admin") for x in cur) <= 1:
        return "last_admin"

    cur = [u for u in cur if (u.get("email","").lower() != (email or "").lower())]
    save_admin_users(cur)

    # re-mirror after deletion
    merged = _merge_users([_norm_admin_user(u) for u in load_admin_users()], _load_doctors_file())
    _mirror_into_db(merged)
    return "ok"

# ---------------------------- Availability Editor ----------------------------
def _availability_editor(prefix: str, initial):
    initial = _coerce_slots(initial)
    cur = {d: {"enabled": False, "start": "09:00", "end": "17:00"} for d in WEEK_DAYS}
    for row in initial:
        d = str(row.get("day", "")).strip().title()[:3] or "Mon"
        s = str(row.get("start", "09:00")).strip() or "09:00"
        e = str(row.get("end", "17:00")).strip() or "17:00"
        if d in cur:
            cur[d]["enabled"] = True
            cur[d]["start"] = s
            cur[d]["end"] = e

    h1, h2, h3, h4 = st.columns([0.7, 1.0, 1.0, 1.0])
    with h1: st.caption("Day")
    with h2: st.caption("Start")
    with h3: st.caption("End")
    with h4: st.caption(" ")

    rows = []
    errs = []
    for day in WEEK_DAYS:
        c1, c2, c3, _ = st.columns([0.7, 1.0, 1.0, 1.0])
        en_key = f"{prefix}_en_{day}"
        st_key = f"{prefix}_st_{day}"
        et_key = f"{prefix}_et_{day}"

        enabled_default = cur[day]["enabled"]
        start_default = _str_to_time(cur[day]["start"], time(9, 0))
        end_default   = _str_to_time(cur[day]["end"], time(17, 0))

        with c1:
            enabled = st.checkbox(day, value=enabled_default, key=en_key)
        with c2:
            t_start = st.time_input("Start", value=start_default, key=st_key, label_visibility="collapsed", step=300)
        with c3:
            t_end = st.time_input("End", value=end_default, key=et_key, label_visibility="collapsed", step=300)

        if enabled and t_end <= t_start:
            st.error(f"{day}: End must be after Start", icon="⚠️")
            errs.append(f"{day}: end<=start")

        if enabled:
            rows.append({"day": day, "start": _time_to_str(t_start), "end": _time_to_str(t_end)})
    return rows, errs

# ---------------------------- Add user panel (writes to admin_users.json) ----------------------------
def _add_user_panel(users_admin: List[Dict[str, Any]]):
    ss = st.session_state
    ss.setdefault("um_pw_value", _generate_password(12))
    ss.setdefault("um_pw_regen", False)
    ss.setdefault("um_pw_widget", ss["um_pw_value"])

    if ss["um_pw_regen"]:
        ss["um_pw_value"] = _generate_password(14)
        ss["um_pw_widget"] = ss["um_pw_value"]
        ss["um_pw_regen"] = False

    st.markdown("<div style='border:1px solid rgba(255,255,255,.14);border-radius:16px;padding:16px;background:linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));margin-bottom:12px;'>", unsafe_allow_html=True)
    _card_header("Add user", "➕")
    st.caption("Saved to data/admin_users.json. You can refine details later in the Details panel.")

    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Full name", placeholder="e.g. Dr. Alice Tan", key="um_add_name")
    with c2:
        email = st.text_input("Email", placeholder="e.g. alice@carelog.local", key="um_add_email")

    col_role, col_pw = st.columns([0.6, 1.4])
    with col_role:
        role = st.selectbox("Role", ROLE_OPTIONS, index=3, key="um_add_role")

    with col_pw:
        st.markdown("**Temporary password**")
        show_pw = st.checkbox("Show password", value=False, key="um_show_pw")
        st.text_input("Password", value=ss["um_pw_widget"], type=("default" if show_pw else "password"),
                      key="um_pw_widget", label_visibility="collapsed")
        if ss["um_pw_widget"] != ss["um_pw_value"]:
            ss["um_pw_value"] = ss["um_pw_widget"]
        g1, g2 = st.columns([0.72, 0.28])
        with g1: st.caption(f"Strength: **{_password_strength_hint(ss['um_pw_value'])}**")
        with g2:
            if st.button("Generate", use_container_width=True, key="um_btn_generate"):
                ss["um_pw_regen"] = True
                st.rerun()

    o1, o2 = st.columns(2)
    with o1:
        specialization = st.text_input("Specialization (optional)", placeholder="e.g. Cardiology", key="um_add_spec")
    with o2:
        qualifications = st.text_input("Qualifications (optional)", placeholder="e.g. MBBS, MRCP", key="um_add_quals")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.session_state.setdefault("um_add_av_inited_for_role", None)
    init_needed = (st.session_state["um_add_av_inited_for_role"] != role)
    init_av = _default_availability_for_role(role) if init_needed else st.session_state.get("um_av_map", [])
    slots, av_errors = _availability_editor("um_av", init_av)
    if init_needed:
        st.session_state["um_add_av_inited_for_role"] = role

    opt1, opt2 = st.columns(2)
    with opt1:
        must_change = st.toggle("Require password change at first login", value=True, key="um_add_must_change")
    with opt2:
        active_now = st.toggle("Activate now", value=True, key="um_add_active_now")

    ac1, ac2 = st.columns(2)
    with ac1:
        cancel = st.button("Cancel", use_container_width=True, key="um_add_cancel")
    with ac2:
        create = st.button("Create user", type="primary", use_container_width=True, key="um_add_create")

    if cancel:
        st.session_state["um_add_open"] = False
        st.rerun()

    if create:
        name_s = (name or "").strip()
        email_s = (email or "").strip()
        pwd = (ss.get("um_pw_value") or "").strip()
        spec_s = (specialization or "").strip()
        quals_s = (qualifications or "").strip()

        errors = []
        if not name_s: errors.append("Name is required.")
        if not email_s: errors.append("Email is required.")
        if email_s and not _valid_email(email_s): errors.append("Email format looks invalid.")
        if any((u.get("email","").lower() == email_s.lower()) for u in users_admin):
            errors.append("Email already exists in admin_users.json.")
        if len(pwd) < 8:
            errors.append("Password must be at least 8 characters.")
        errors.extend(av_errors)

        if errors:
            for e in errors: st.error(e)
        else:
            # Assign public code from current DB (so numbering is consistent)
            db = load_db()
            public_code = next_role_code(db, role)
            # Build new user row for admin_users.json
            new_user = {
                "id": email_s,  # keep id stable; will be coerced when mirrored
                "code": public_code,
                "name": name_s,
                "email": email_s,
                "role": role,
                "pwd": pwd,
                "locked": not active_now,
                "note": "",
                "must_change_pwd": bool(must_change),
                "specialization": spec_s,
                "qualifications": quals_s,
                "availability": slots,
            }
            # Save to data/admin_users.json
            current = [u for u in load_admin_users()]
            current.append(new_user)
            save_admin_users(current)

            # Mirror into app DB
            merged = _merge_users([_norm_admin_user(u) for u in load_admin_users()], _load_doctors_file())
            _mirror_into_db(merged)

            st.session_state["um_add_open"] = False
            st.success(f"Created {new_user['name']} ({new_user['code']}) · {new_user['role'].replace('_',' ').title()} "
                       f"· {'Active' if active_now else 'Deactivated'} · {len(slots)} day(s) available")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------- main render ----------------------------
def render():
    st.session_state.setdefault("um_add_open", False)
    st.session_state.setdefault("um_page", 1)

    st.markdown(
        "<h3 style='display:flex;align-items:center;gap:10px;margin:0 0 6px 0;'>"
        "👥 <span>User Management</span></h3>"
        "<p style='margin:0;opacity:.8;'>Linked to <code>data/admin_users.json</code> and enriched with <code>data/doctors.json</code>. Edits save to admin_users.json.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # Load external sources
    admin_users = [_norm_admin_user(u) for u in load_admin_users()]
    doctors = _load_doctors_file()
    merged = _merge_users(admin_users, doctors)
    _mirror_into_db(merged)  # keep rest of app in sync

    data_root = _data_dir().as_posix()
    st.caption(f"Sources → **{data_root}/admin_users.json** (+ **{data_root}/doctors.json**) • Total loaded: **{len(merged)}**")

    # KPIs (using merged)
    c1, c2, c3, c4 = st.columns(4)
    with c1: _kpi("Total", str(len(merged)))
    with c2: _kpi("Admins", str(sum(u.get("role") == "admin" for u in merged)))
    with c3: _kpi("Clinical (Dr+Nurse)", str(sum(u.get("role") in ("doctor", "nurse") for u in merged)))
    with c4: _kpi("Deactivated", str(sum(u.get("locked") for u in merged)))

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Top actions
    top_l, top_r = st.columns([0.45, 1.55])
    with top_l:
        if st.button("➕ Add user", type="primary", use_container_width=True):
            st.session_state["um_add_open"] = True
    with top_r:
        with st.expander("Bulk import / export (admin_users.json)", expanded=False):
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                up = st.file_uploader(
                    "Import CSV (name,email,role,locked[,specialization][,qualifications][,availability])",
                    type=["csv"]
                )
                if up is not None:
                    try:
                        df = pd.read_csv(up)
                        required = {"name","email","role","locked"}
                        if not required.issubset(df.columns):
                            st.error("CSV must include: name, email, role, locked")
                        else:
                            base = [u for u in load_admin_users()]
                            updated = 0
                            for _, r in df.iterrows():
                                try:
                                    role = str(r["role"]).lower()
                                    if role not in ROLE_OPTIONS:
                                        continue
                                    email = str(r["email"]).strip()
                                    name = str(r["name"]).strip()
                                    if not email or not _valid_email(email):
                                        continue

                                    avail = []
                                    if "availability" in df.columns and not pd.isna(r.get("availability")):
                                        try:
                                            parsed = json.loads(str(r["availability"]))
                                            if isinstance(parsed, list):
                                                avail = _coerce_slots(parsed)
                                        except Exception:
                                            avail = []

                                    exists = next((u for u in base if (u.get("email","").lower()==email.lower())), None)
                                    if exists:
                                        exists.update({
                                            "name": name,
                                            "email": email,
                                            "role": role,
                                            "locked": bool(r["locked"]),
                                            "specialization": str(r["specialization"]) if "specialization" in df.columns and not pd.isna(r["specialization"]) else exists.get("specialization",""),
                                            "qualifications": str(r["qualifications"]) if "qualifications" in df.columns and not pd.isna(r["qualifications"]) else exists.get("qualifications",""),
                                            "availability": avail if avail else exists.get("availability", []),
                                        })
                                    else:
                                        # require a public code
                                        code = next_role_code(load_db(), role)
                                        base.append({
                                            "id": email, "code": code, "name": name, "email": email, "role": role,
                                            "locked": bool(r["locked"]), "pwd": "changeme123", "must_change_pwd": True,
                                            "specialization": str(r["specialization"]) if "specialization" in df.columns and not pd.isna(r["specialization"]) else "",
                                            "qualifications": str(r["qualifications"]) if "qualifications" in df.columns and not pd.isna(r["qualifications"]) else "",
                                            "availability": avail,
                                            "note": "",
                                        })
                                    updated += 1
                                except Exception:
                                    continue
                            save_admin_users(base)
                            merged = _merge_users([_norm_admin_user(u) for u in load_admin_users()], _load_doctors_file())
                            _mirror_into_db(merged)
                            st.success(f"Imported/updated {updated} user(s) to admin_users.json.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Import failed: {e}")
            with col_b2:
                exp = pd.DataFrame([{
                    "name": u.get("name"),
                    "email": u.get("email"),
                    "role": u.get("role"),
                    "locked": bool(u.get("locked", False)),
                    "specialization": u.get("specialization", ""),
                    "qualifications": u.get("qualifications", ""),
                    "availability": json.dumps(u.get("availability", []), ensure_ascii=False),
                } for u in admin_users])  # export only admin_users.json rows
                st.download_button(
                    "Export CSV (admin_users.json)",
                    data=exp.to_csv(index=False).encode("utf-8"),
                    file_name=f"admin_users_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    use_container_width=True
                )

    if st.session_state["um_add_open"]:
        _add_user_panel([u for u in load_admin_users()])  # pass the current admin_users list for duplicate checks

    # Filters
    f1, f2, f3 = st.columns([1.6, 0.8, 0.8])
    with f1:
        search = st.text_input("Search", placeholder="Name or email…", key="um_query")
    with f2:
        role_filter = st.multiselect("Role", ROLE_OPTIONS, default=ROLE_OPTIONS, key="um_role_filter")
    with f3:
        status_filter = st.selectbox("Status", ["All", "Active", "Deactivated"], index=0, key="um_status_filter")

    def _match(u: Dict[str, Any]) -> bool:
        if u.get("role") not in role_filter:
            return False
        if status_filter == "Active" and u.get("locked"):
            return False
        if status_filter == "Deactivated" and not u.get("locked"):
            return False
        s = (search or "").strip().lower()
        if not s:
            return True
        return s in (u.get("name", "").lower()) or s in (u.get("email", "").lower())

    filtered = [u for u in merged if _match(u)]

    # Table rows
    rows = [{
        "ID": u.get("code", "—"),
        "NumID": _coerce_int_id(u.get("id")),
        "Name": u.get("name"),
        "Email": u.get("email"),
        "Role": u.get("role"),
        "Specialization": u.get("specialization", "") or "—",
        "Qualifications": u.get("qualifications", "") or "—",
        "Status": "Deactivated" if u.get("locked") else "Active",
        "Source": "Admin Users" if u.get("_source") == "admin_users" else "Doctors.json",
    } for u in filtered]

    if rows:
        def _code_n(row: Dict[str, Any]) -> int:
            pref = ROLE_PREFIX.get((row.get("Role") or "").lower(), "")
            return extract_role_number(row.get("ID",""), pref)
        table_df = pd.DataFrame(rows)
        table_df["__n"] = table_df.apply(lambda r: _code_n(r), axis=1)
        table_df = table_df.sort_values(["Role","__n"], kind="mergesort", ignore_index=True).drop(columns=["__n"])
    else:
        table_df = pd.DataFrame(columns=["ID","NumID","Name","Email","Role","Specialization","Qualifications","Status","Source"])

    _card_header("Users", "🗂️")
    st.caption("Select a user to view and edit details.")
    if table_df.empty:
        st.info("No matching users.")
        return

    st.dataframe(table_df.drop(columns=["NumID"]), use_container_width=True, hide_index=True)

    # pick current
    display_map = {
        f"{row['ID']} – {row['Name']} ({row['Email']})": int(row["NumID"])
        for _, row in table_df.iterrows()
    }
    options = list(display_map.keys())
    prev_label = st.session_state.get("um_selected_label")
    default_index = options.index(prev_label) if prev_label in options else 0
    selected_label = st.selectbox("Select a user", options, index=default_index if options else 0, key="um_selected_label")
    selected_numid = display_map.get(selected_label)

    # find selected in merged
    current = next((u for u in merged if _coerce_int_id(u.get("id")) == selected_numid), None)
    if not current:
        st.info("Select a user above.")
        return

    read_only = (current.get("_source") != "admin_users")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    _card_header("Details", "🧾")

    icon = _role_icon(current.get("role"))
    status_badge = _badge("Deactivated", "err") if current.get("locked") else _badge("Active", "ok")
    spec_lbl = current.get("specialization") or "—"
    quals_lbl = current.get("qualifications") or "—"
    avail_lbl = f"{len(current.get('availability', []))} day(s)"

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
          <div style="width:48px;height:48px;border-radius:999px;background:rgba(255,255,255,.08);
                      display:flex;align-items:center;justify-content:center;font-size:24px;">{icon}</div>
          <div>
            <div style="font-size:18px;font-weight:800">{current.get('name')}</div>
            <div style="opacity:.85">{current.get('email')}</div>
          </div>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
          {_badge('ID ' + (current.get('code') or '—'), 'info')}
          {_badge('UID ' + str(_coerce_int_id(current.get('id'))), 'neutral')}
          {_badge((current.get('role') or '').replace('_',' ').title(), 'info')}
          {status_badge}
          {_badge('Spec: ' + spec_lbl, 'neutral')}
          {_badge('Quals: ' + quals_lbl, 'neutral')}
          {_badge('Avail: ' + avail_lbl, 'neutral')}
          {_badge('Source: ' + ('Admin Users' if current.get('_source')=='admin_users' else 'Doctors.json'), 'neutral')}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # If doctor comes only from doctors.json → let admin import for editing
    if read_only:
        st.warning(
            "This user comes from data/doctors.json and is read-only here. "
            "Click **Import to Admin Users** to make it editable (writes to data/admin_users.json)."
        )
        if st.button("Import to Admin Users", type="primary"):
            base = [u for u in load_admin_users()]
            if any((u.get("email","").lower() == (current.get("email","") or "").lower()) for u in base):
                st.info("Already exists in admin_users.json; please Reload.")
            else:
                code = current.get("code") or next_role_code(load_db(), "doctor")
                to_add = {
                    "id": current.get("email") or current.get("id"),
                    "code": code,
                    "name": current.get("name",""),
                    "email": current.get("email",""),
                    "role": "doctor",
                    "locked": current.get("locked", False),
                    "pwd": current.get("pwd","changeme123"),
                    "must_change_pwd": True,
                    "specialization": current.get("specialization",""),
                    "qualifications": current.get("qualifications",""),
                    "availability": _coerce_slots(current.get("availability", [])),
                    "note": current.get("note",""),
                }
                base.append(to_add)
                save_admin_users(base)
                merged2 = _merge_users([_norm_admin_user(u) for u in load_admin_users()], _load_doctors_file())
                _mirror_into_db(merged2)
                st.success("Imported. Reloading…")
                st.rerun()

    tabs = st.tabs(["Profile", "Security", "Availability", "Notes", "Danger Zone"])

    # Profile (save to admin_users.json)
    with tabs[0]:
        st.caption("Basic details and role. (Saves to data/admin_users.json)")
        with st.form("um_profile"):
            name = st.text_input("Full name", value=current.get("name", ""), disabled=read_only)
            email = st.text_input("Email", value=current.get("email", ""), disabled=read_only)
            role = st.selectbox("Role", ROLE_OPTIONS, index=ROLE_OPTIONS.index(current.get("role", "staff")), disabled=read_only)
            spec = st.text_input("Specialization (optional)", value=current.get("specialization", ""), disabled=read_only)
            quals = st.text_input("Qualifications (optional)", value=current.get("qualifications", ""), disabled=read_only)
            active = st.toggle("Active (can sign in)", value=not current.get("locked", False), disabled=read_only)
            submitted = st.form_submit_button("Save changes", type="primary", disabled=read_only)
        if submitted:
            if not name or not email:
                st.error("Name and email are required.")
            elif any((u.get("email","").lower()==email.lower()) and (u is not current) for u in merged if u.get("_source")=="admin_users"):
                st.error("Email already exists for another user.")
            else:
                base = [u for u in load_admin_users()]
                row = next((u for u in base if (u.get("email","").lower()==current.get("email","").lower())), None)
                if row:
                    row["name"] = name.strip()
                    row["email"] = email.strip()
                    row["role"] = role
                    row["locked"] = not active
                    row["specialization"] = spec.strip()
                    row["qualifications"] = quals.strip()
                    # keep code; assign if missing
                    if not row.get("code"):
                        row["code"] = current.get("code") or next_role_code(load_db(), role)
                    save_admin_users(base)
                    merged2 = _merge_users([_norm_admin_user(u) for u in load_admin_users()], _load_doctors_file())
                    _mirror_into_db(merged2)
                    st.success("Profile updated.")
                    st.rerun()

    # Security
    with tabs[1]:
        st.caption("Reset password or clear lockouts. (Writes to admin_users.json)")
        show = st.toggle("Show password", value=False, key="sec_show", disabled=read_only)
        pw1 = st.text_input("New password", type=("default" if show else "password"), disabled=read_only)
        pw2 = st.text_input("Confirm password", type=("default" if show else "password"), disabled=read_only)
        require_change = st.toggle("Require password change at next login", value=bool(current.get("must_change_pwd", True)), disabled=read_only)
        col_s1, col_s2 = st.columns([1, 1])
        with col_s1:
            if st.button("🔑 Update password", use_container_width=True, disabled=read_only):
                if not pw1:
                    st.error("Password cannot be empty.")
                elif pw1 != pw2:
                    st.error("Passwords do not match.")
                else:
                    base = [u for u in load_admin_users()]
                    row = next((u for u in base if (u.get("email","").lower()==current.get("email","").lower())), None)
                    if row:
                        row["pwd"] = pw1
                        row["must_change_pwd"] = bool(require_change)
                        save_admin_users(base)
                        merged2 = _merge_users([_norm_admin_user(u) for u in load_admin_users()], _load_doctors_file())
                        _mirror_into_db(merged2)
                        st.success("Password updated.")
                        st.rerun()
        with col_s2:
            if st.button("🧹 Clear lockouts", use_container_width=True, disabled=read_only):
                # lockouts are tracked in carelog.json; clearing doesn't need admin_users.json
                db = load_db()
                la = db.get("login_attempts", {})
                em = current.get("email","")
                if em in la:
                    la[em]["fails"] = 0
                    db["login_attempts"] = la
                    save_db(db)
                st.success("Login attempts cleared.")

    # Availability
    with tabs[2]:
        st.caption("Weekly availability for scheduling. (Saves to admin_users.json)")
        slots_initial = _coerce_slots(current.get("availability"))
        slots_new, errs = _availability_editor(f"um_edit_av_{_coerce_int_id(current.get('id'))}", slots_initial)
        if errs:
            for e in errs: st.error(e)
        if st.button("Save availability", type="primary", key=f"um_save_av_{_coerce_int_id(current.get('id'))}", disabled=read_only):
            base = [u for u in load_admin_users()]
            row = next((u for u in base if (u.get("email","").lower()==current.get("email","").lower())), None)
            if row:
                row["availability"] = slots_new
                save_admin_users(base)
                merged2 = _merge_users([_norm_admin_user(u) for u in load_admin_users()], _load_doctors_file())
                _mirror_into_db(merged2)
                st.success(f"Availability saved ({len(slots_new)} day(s)).")
                st.rerun()

    # Notes
    with tabs[3]:
        st.caption("Private note (only visible to admins). (Saves to admin_users.json)")
        note_val = st.text_area("Notes", value=current.get("note", ""), height=120, disabled=read_only)
        if st.button("Save note", type="primary", disabled=read_only):
            base = [u for u in load_admin_users()]
            row = next((u for u in base if (u.get("email","").lower()==current.get("email","").lower())), None)
            if row:
                row["note"] = (note_val or "").strip()
                save_admin_users(base)
                merged2 = _merge_users([_norm_admin_user(u) for u in load_admin_users()], _load_doctors_file())
                _mirror_into_db(merged2)
                st.success("Note saved.")
                st.rerun()

    # Danger Zone: delete (only admin_users.json entries)
    with tabs[4]:
        st.warning("Deleting here removes the record from data/admin_users.json. Doctors that exist only in doctors.json are read-only and cannot be deleted here.")
        if current.get("_source") != "admin_users":
            st.info("This user is from doctors.json — import to Admin Users first if you want to manage or delete it here.")
        else:
            confirm = st.text_input("Type the user's email to confirm deletion", placeholder=current.get("email",""))
            can_delete = confirm.strip().lower() == (current.get("email","").lower())
            if st.button("Delete this user", type="primary", disabled=not can_delete):
                # guard rails: prevent deleting last admin
                result = _delete_user_and_cleanup_admin_users(current.get("email",""))
                if result == "ok":
                    st.success("User deleted from admin_users.json.")
                    st.rerun()
                elif result == "last_admin":
                    st.error("Cannot delete the last remaining admin.")
                elif result == "self":
                    st.error("You cannot delete the account you’re signed in with.")
                else:
                    st.error("User not found in admin_users.json.")
