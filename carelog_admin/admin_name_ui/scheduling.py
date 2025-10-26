# admin_name_ui/scheduling.py
from __future__ import annotations

from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List, Optional
import calendar
import json

import streamlit as st
import pandas as pd

from admin_name_utils.storage import load_db, save_db

WEEK_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ---------------- UI bits ----------------
def _card_header(title: str, emoji: str = ""):
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:10px;">
               <div style="font-size:20px">{emoji}</div>
               <h4 style="margin:0;">{title}</h4>
           </div>""",
        unsafe_allow_html=True,
    )


# ---------------- helpers ----------------
def _fmt_time_iso(d: date, t: time) -> str:
    return datetime.combine(d, t).isoformat(timespec="minutes") + "Z"

def _parse_iso(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))

def _overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return (a_start < b_end) and (b_start < a_end)

def _short_user(u: Dict[str, Any]) -> str:
    code = u.get("code") or str(u.get("id"))
    return f"{code} – {u.get('name','')}"

def _room_label(r: Dict[str, Any]) -> str:
    parts = []
    code = r.get("code") or r.get("id")
    if code is not None:
        parts.append(str(code))
    nm = r.get("name")
    if nm:
        parts.append(nm)
    typ = r.get("type")
    if typ:
        parts.append(f"({typ})")
    return " ".join(parts) or f"Room #{r.get('id','?')}"

# --- availability normalizer (fix for your error)
def _normalize_availability(slots_raw) -> List[Dict[str, str]]:
    """
    Coerce availability into list of dicts: [{"day":"Mon","start":"09:00","end":"17:00"}, ...]
    Accepts: None | list[dict/other] | JSON string.
    Invalid rows are skipped.
    """
    if not slots_raw:
        return []
    slots = slots_raw
    if isinstance(slots_raw, str):
        try:
            slots = json.loads(slots_raw)
        except Exception:
            return []
    out: List[Dict[str, str]] = []
    if isinstance(slots, list):
        for x in slots:
            if isinstance(x, dict):
                d = (str(x.get("day", "")).strip().title()[:3] or "Mon")
                s = (str(x.get("start", "09:00")).strip() or "09:00")
                e = (str(x.get("end", "17:00")).strip() or "17:00")
                out.append({"day": d, "start": s, "end": e})
    return out

def _user_availability_ok(user: Dict[str, Any], d: date, start_t: time, end_t: time) -> tuple[bool, str]:
    """
    Works for any provider/nurse alike. Normalizes stored availability first.
    """
    slots = _normalize_availability(user.get("availability", []))
    dow = WEEK_DAYS[d.weekday()]
    day_slots = [s for s in slots if str(s.get("day")) == dow]
    if not day_slots:
        role = (user.get("role") or "user").title()
        return False, f"{role} is not available on {dow}."

    for s in day_slots:
        try:
            sh, sm = map(int, str(s.get("start", "09:00")).split(":"))
            eh, em = map(int, str(s.get("end", "17:00")).split(":"))
            s_start = time(sh, sm)
            s_end = time(eh, em)
            if s_start <= start_t and end_t <= s_end:
                return True, ""
        except Exception:
            continue

    role = (user.get("role") or "user").title()
    return False, f"Chosen time is outside {role.lower()}’s availability for {dow}."

def _next_quarter(now: Optional[datetime] = None) -> time:
    if now is None:
        now = datetime.now()
    minutes = ((now.minute // 15) + 1) * 15
    adj = now.replace(second=0, microsecond=0) + timedelta(minutes=(minutes - now.minute))
    return time(adj.hour, adj.minute)

def _conflicts_for(db: Dict[str, Any], kind: str, entity_id: int,
                   start_dt: datetime, end_dt: datetime,
                   ignore_appt_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    kind: 'doctor' | 'patient' | 'room' | 'nurse'
    NOTE: we store BOTH doctors and psychological counselors in doctor_id for compatibility.
    """
    hits = []
    for a in db.get("appointments", []):
        if ignore_appt_id and a.get("id") == ignore_appt_id:
            continue

        if kind == "doctor" and a.get("doctor_id") != entity_id:
            continue
        if kind == "patient" and a.get("patient_id") != entity_id:
            continue
        if kind == "room" and a.get("room_id") != entity_id:
            continue
        if kind == "nurse" and a.get("nurse_id") != entity_id:
            continue

        try:
            a_s = _parse_iso(a["start_iso"])
            a_e = _parse_iso(a.get("end_iso") or a["start_iso"])
        except Exception:
            continue

        if _overlap(start_dt, end_dt, a_s, a_e):
            hits.append(a)
    return hits

def _next_appt_id(db: Dict[str, Any]) -> int:
    return max([a.get("id", 0) for a in db.get("appointments", [])] + [0]) + 1

# ---- tiny lookups for calendar chips
def _user_by_id(db, uid):  # any user
    return next((u for u in db.get("users", []) if u.get("id") == uid), None)

def _patient_by_id(db, pid):
    return next((p for p in db.get("patients", []) if p.get("id") == pid), None)

def _room_by_id(db, rid):
    return next((r for r in db.get("rooms", []) if r.get("id") == rid), None)

# ---------------- Calendar (week & month) ----------------
_STATUS_BG = {
    "booked":    "linear-gradient(180deg, rgba(99,179,237,.85), rgba(99,179,237,.65))",
    "checkedin": "linear-gradient(180deg, rgba(234,179,8,.85), rgba(234,179,8,.60))",
    "done":      "linear-gradient(180deg, rgba(34,197,94,.85), rgba(34,197,94,.60))",
    "cancelled": "linear-gradient(180deg, rgba(239,68,68,.85), rgba(239,68,68,.60))",
}

def _ldt(iso: str) -> datetime:
    return _parse_iso(iso).astimezone()

def _week_calendar_html(db, base_day: date) -> str:
    start_h, end_h, step = 8, 20, 30  # 08:00–20:00
    slots = [time(h, m) for h in range(start_h, end_h) for m in (0, step)]
    monday = base_day - timedelta(days=base_day.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    by_day: Dict[date, List[Dict[str, Any]]] = {d: [] for d in days}
    for a in db.get("appointments", []):
        try:
            d = _ldt(a["start_iso"]).date()
        except Exception:
            continue
        if d in by_day:
            by_day[d].append(a)

    def block_css(a):
        s = _ldt(a["start_iso"])
        e = _ldt(a["end_iso"]) if a.get("end_iso") else s + timedelta(minutes=30)
        span = (end_h - start_h) * 60
        st_min = s.hour * 60 + s.minute
        en_min = e.hour * 60 + e.minute
        top = max(0, (st_min - start_h * 60) / span * 100)
        ht = max(5, (en_min - st_min) / span * 100)
        bg = _STATUS_BG.get(a.get("status", "booked"), _STATUS_BG["booked"])
        return f"top:{top:.2f}%;height:{ht:.2f}%;background:{bg};"

    html = """
    <style>
      .cal-wrap { border:1px solid rgba(255,255,255,.15); border-radius:14px; overflow:hidden; }
      .cal-head { display:grid; grid-template-columns:80px repeat(7, 1fr); background:rgba(255,255,255,.05); }
      .cal-head div { padding:10px 8px; font-weight:700; border-right:1px solid rgba(255,255,255,.08); }
      .cal-body { display:grid; grid-template-columns:80px repeat(7, 1fr); }
      .cal-times { background:rgba(255,255,255,.03); border-right:1px solid rgba(255,255,255,.08); }
      .cal-slot { height:26px; font-size:12px; opacity:.8; padding:2px 8px; border-top:1px dashed rgba(255,255,255,.07); }
      .cal-day  { position:relative; border-right:1px solid rgba(255,255,255,.08); }
      .cal-day:last-child { border-right:none; }
      .cal-grid { position:relative; height:520px; }
      .cal-apt  { position:absolute; left:6px; right:6px; border-radius:10px; padding:6px 8px; color:#0b1220; box-shadow:0 1px 2px rgba(0,0,0,.28); }
      .cal-apt .t { font-weight:700; font-size:12px; }
      .cal-apt .s { font-size:12px; opacity:.92; }
      .cal-apt .m { font-size:11px; opacity:.85; margin-top:2px; }
    </style>
    """
    html += "<div class='cal-wrap'>"
    html += "<div class='cal-head'><div></div>" + "".join(
        f"<div>{d.strftime('%a %d %b')}</div>" for d in days
    ) + "</div>"
    html += "<div class='cal-body'>"
    html += "<div class='cal-times'>" + "".join(
        f"<div class='cal-slot'>{t.strftime('%H:%M')}</div>" for t in slots
    ) + "</div>"

    for d in days:
        html += "<div class='cal-day'><div class='cal-grid'>"
        for a in by_day.get(d, []):
            s = _ldt(a["start_iso"])
            e = _ldt(a["end_iso"]) if a.get("end_iso") else s + timedelta(minutes=30)
            p = _patient_by_id(db, a.get("patient_id")) or {}
            prov = _user_by_id(db, a.get("doctor_id")) or {}
            nur = _user_by_id(db, a.get("nurse_id")) or {}
            room = _room_by_id(db, a.get("room_id"))
            meta = []
            if room: meta.append(f"Room {room.get('code')}")
            if nur:  meta.append(f"Nurse {nur.get('name','')}")
            meta_txt = " • ".join(meta)
            html += (
                f"<div class='cal-apt' style='{block_css(a)}'>"
                f"  <div class='t'>{p.get('name','')}</div>"
                f"  <div class='s'>{s.strftime('%H:%M')}–{e.strftime('%H:%M')} · {prov.get('name','')}</div>"
                f"  <div class='m'>{meta_txt}</div>"
                f"</div>"
            )
        html += "</div></div>"
    html += "</div></div>"
    return html

def _month_calendar_html(db, base_month: date) -> str:
    first = date(base_month.year, base_month.month, 1)
    _, last_day = calendar.monthrange(base_month.year, base_month.month)
    last = date(base_month.year, base_month.month, last_day)
    cal = calendar.Calendar(firstweekday=0)
    weeks = list(cal.monthdatescalendar(base_month.year, base_month.month))

    by_day: Dict[date, List[Dict[str, Any]]] = {}
    for a in db.get("appointments", []):
        try:
            d = _ldt(a["start_iso"]).date()
        except Exception:
            continue
        if first <= d <= last:
            by_day.setdefault(d, []).append(a)

    html = """
    <style>
      .mo-wrap { border:1px solid rgba(255,255,255,.15); border-radius:14px; overflow:hidden; }
      .mo-head { display:grid; grid-template-columns:repeat(7, 1fr); background:rgba(255,255,255,.05); }
      .mo-head div { padding:10px 8px; font-weight:700; border-right:1px solid rgba(255,255,255,.08); }
      .mo-week { display:grid; grid-template-columns:repeat(7, 1fr); min-height:120px; }
      .mo-day  { border-right:1px solid rgba(255,255,255,.08); border-top:1px solid rgba(255,255,255,.08); padding:6px; }
      .mo-day:last-child { border-right:none; }
      .mo-num  { font-size:12px; opacity:.9; margin-bottom:4px; }
      .chip    { margin:3px 0; padding:4px 6px; border-radius:8px; font-size:12px; color:#0b1220;
                 background:rgba(99,179,237,.75); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .chip.done { background:rgba(34,197,94,.80); }
      .chip.cancelled { background:rgba(239,68,68,.80); }
      .chip.checkedin { background:rgba(234,179,8,.85); }
      .dim { opacity:.45; }
    </style>
    """
    html += "<div class='mo-wrap'>"
    html += "<div class='mo-head'>" + "".join(f"<div>{d}</div>" for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]) + "</div>"
    for w in weeks:
        html += "<div class='mo-week'>"
        for d in w:
            dim = " dim" if d.month != base_month.month else ""
            html += f"<div class='mo-day{dim}'><div class='mo-num'>{d.day}</div>"
            for a in by_day.get(d, []):
                p = _patient_by_id(db, a.get("patient_id")) or {}
                s = _ldt(a["start_iso"])
                cls = a.get("status", "booked")
                html += f"<div class='chip {cls}'>{s.strftime('%H:%M')} · {p.get('name','')}</div>"
            html += "</div>"
        html += "</div>"
    html += "</div>"
    return html

def _render_calendar_section(db):
    st.markdown("### 📆 Calendar")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        view = st.radio("View", ["Week", "Month"], horizontal=True)
    with c3:
        colL, colR = st.columns(2)
        with colL:
            if st.button("◀ Prev", use_container_width=True):
                st.session_state["sched_cal_offset"] = st.session_state.get("sched_cal_offset", 0) - 1
                st.rerun()
        with colR:
            if st.button("Next ▶", use_container_width=True):
                st.session_state["sched_cal_offset"] = st.session_state.get("sched_cal_offset", 0) + 1
                st.rerun()

    off = st.session_state.get("sched_cal_offset", 0)
    if view == "Week":
        base = date.today() + timedelta(weeks=off)
        st.markdown(_week_calendar_html(db, base), unsafe_allow_html=True)
        st.caption("30-minute grid • 08:00–20:00 · Colors: Booked / Checked-in / Done / Cancelled.")
    else:
        base = date.today().replace(day=1)
        y = base.year + (base.month - 1 + off) // 12
        m = (base.month - 1 + off) % 12 + 1
        st.markdown(_month_calendar_html(db, date(y, m, 1)), unsafe_allow_html=True)
        st.caption("Compact month view with chips per day.")

# ---------------- render ----------------
def render():
    db = load_db()

    st.markdown(
        "<h3 style='display:flex;align-items:center;gap:10px;margin:0 0 6px 0;'>"
        "🗓️ <span>Appointment & Scheduling</span></h3>"
        "<p style='margin:0;opacity:.8;'>Allocate patient, provider (doctor/psychological counselor), nurse and room. "
        "Manual times with availability and conflict checks.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ---------- Prefill coming from Rooms & Resources ----------
    prefill = st.session_state.get("sched_prefill", {})
    pre_room_id = prefill.get("room_id")
    pre_date = prefill.get("date")
    pre_start = prefill.get("start")
    pre_end = prefill.get("end")

    # ---------- Create ----------
    with st.expander("➕ Create Appointment", expanded=True):
        _card_header("Create Appointment", "📅")

        patients = db.get("patients", [])
        if not patients:
            st.info("No patients found. Add patients first.")
            return

        users = db.get("users", [])
        doctors = [u for u in users if u.get("role") == "doctor"]
        counselors = [u for u in users if u.get("role") == "psychological_counselor"]
        nurses = [u for u in users if u.get("role") == "nurse"]

        if not doctors and not counselors:
            st.info("No providers found. Add doctors or psychological counselors first.")
            return
        if not nurses:
            st.warning("No nurses found. Add nurses in User Management before booking.")
            return

        rooms = db.get("rooms", [])
        if not rooms:
            st.warning("No rooms found. Add rooms in Rooms & Resources before booking.")
            return

        # --- Provider type + provider select ---
        provider_type = st.selectbox("Provider type", ["Doctor", "Psychological counselor"], index=0, key="sched_provider_type")
        provider_pool = doctors if provider_type == "Doctor" else counselors
        if not provider_pool:
            st.error(f"No {provider_type.lower()}s found.")
            return

        patient = st.selectbox(
            "Patient",
            patients,
            format_func=lambda p: f"{p.get('id')} - {p.get('name','')}",
            key="sched_sel_patient",
        )
        provider = st.selectbox(
            "Provider",
            provider_pool,
            format_func=_short_user,
            key="sched_sel_provider",
        )
        nurse = st.selectbox(
            "Nurse",
            nurses,
            format_func=_short_user,
            key="sched_sel_nurse",
        )

        # Room with preselect
        default_room_index = 0
        if pre_room_id is not None:
            for i, r in enumerate(rooms):
                if int(r.get("id")) == int(pre_room_id):
                    default_room_index = i
                    break
        room = st.selectbox(
            "Room",
            rooms,
            index=default_room_index if rooms else 0,
            format_func=_room_label,
            key="sched_sel_room",
        )

        # Date with prefill
        default_date = date.today()
        try:
            if pre_date:
                default_date = date.fromisoformat(str(pre_date))
        except Exception:
            pass
        d_val: date = st.date_input("Date", value=default_date, key="sched_date")

        # Times with prefill
        def _parse_hhmm(s: Optional[str], fallback: time) -> time:
            try:
                if not s:
                    return fallback
                hh, mm = s.split(":")
                return time(int(hh), int(mm))
            except Exception:
                return fallback

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            start_default = _parse_hhmm(pre_start, _next_quarter())
            t_start: time = st.time_input("Start", value=start_default, step=900, key="sched_start")
        with col_t2:
            t_end_default = _parse_hhmm(pre_end, (datetime.combine(date.today(), start_default) + timedelta(minutes=30)).time())
            t_end: time = st.time_input("End", value=t_end_default, step=900, key="sched_end")

        note = st.text_input("Notes (optional)", placeholder="Reason / location / remarks", key="sched_note")

        if st.button("Book Appointment", type="primary", use_container_width=True, key="sched_book_btn"):
            if t_end <= t_start:
                st.error("End time must be after Start time.")
                st.stop()

            ok_p, reason_p = _user_availability_ok(provider, d_val, t_start, t_end)
            if not ok_p:
                st.error(reason_p)
                st.stop()

            ok_n, reason_n = _user_availability_ok(nurse, d_val, t_start, t_end)
            if not ok_n:
                st.error(reason_n)
                st.stop()

            start_iso = _fmt_time_iso(d_val, t_start)
            end_iso = _fmt_time_iso(d_val, t_end)
            start_dt = _parse_iso(start_iso)
            end_dt = _parse_iso(end_iso)

            prov_conflicts = _conflicts_for(db, "doctor", int(provider["id"]), start_dt, end_dt)
            pat_conflicts = _conflicts_for(db, "patient", int(patient["id"]), start_dt, end_dt)
            room_conflicts = _conflicts_for(db, "room", int(room["id"]), start_dt, end_dt)
            nurse_conflicts = _conflicts_for(db, "nurse", int(nurse["id"]), start_dt, end_dt)

            has_err = False
            if prov_conflicts:
                has_err = True
                st.error(f"{provider_type} already has an overlapping appointment.")
            if pat_conflicts:
                has_err = True
                st.error("Patient already has an overlapping appointment.")
            if room_conflicts:
                has_err = True
                st.error("Room is already booked in that time range.")
            if nurse_conflicts:
                has_err = True
                st.error("Nurse is already allocated in that time range.")
            if has_err:
                st.stop()

            appt = {
                "id": _next_appt_id(db),
                "patient_id": int(patient["id"]),
                "doctor_id": int(provider["id"]),  # provider id lives here (doctor or counselor)
                "provider_role": provider.get("role", "doctor"),
                "nurse_id": int(nurse["id"]),
                "room_id": int(room["id"]),
                "start_iso": start_iso,
                "end_iso": end_iso,
                "status": "booked",
                "note": (note or "").strip(),
                "created_by": st.session_state.get("user", {}).get("id"),
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
            all_appts = db.get("appointments", [])
            all_appts.append(appt)
            db["appointments"] = all_appts
            save_db(db)
            st.session_state.pop("sched_prefill", None)
            st.success("Appointment booked.")
            st.rerun()

    if "sched_prefill" in st.session_state:
        st.session_state.pop("sched_prefill", None)

    # ---------- Today ----------
    colA, colB = st.columns([1.1, 1.2])

    with colA:
        _card_header("Today's Appointments", "📌")
        today = date.today()
        rows = []
        rooms = db.get("rooms", [])
        users = db.get("users", [])

        for a in db.get("appointments", []):
            try:
                sdt = _parse_iso(a["start_iso"])
                if sdt.date() != today:
                    continue
                edt = _parse_iso(a.get("end_iso") or a["start_iso"])
            except Exception:
                continue
            p = next((p for p in db.get("patients", []) if p.get("id") == a.get("patient_id")), {})
            provider = next((u for u in users if u.get("id") == a.get("doctor_id")), {})
            n = next((u for u in users if u.get("role") == "nurse" and u.get("id") == a.get("nurse_id")), {})
            r = next((r for r in rooms if r.get("id") == a.get("room_id")), {})
            rows.append({
                "Time": f"{sdt.strftime('%H:%M')}–{edt.strftime('%H:%M')}",
                "Patient": p.get("name", f"#{a.get('patient_id')}"),
                "Provider": provider.get("name", f"#{a.get('doctor_id')}"),
                "Nurse": n.get("name", f"#{a.get('nurse_id')}") if a.get("nurse_id") else "—",
                "Room": (r.get('name') or r.get('code') or f"#{a.get('room_id')}") if r else "—",
                "Status": a.get("status", "booked").title(),
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No appointments today.")

    # ---------- Upcoming (7 days) ----------
    with colB:
        _card_header("Upcoming (next 7 days)", "⏭️")
        base = datetime.now()
        horizon = base + timedelta(days=7)
        rows = []
        rooms = db.get("rooms", [])
        users = db.get("users", [])

        for a in sorted(db.get("appointments", []), key=lambda x: x.get("start_iso", "")):
            try:
                sdt = _parse_iso(a["start_iso"])
                if not (base.date() <= sdt.date() <= horizon.date()):
                    continue
                edt = _parse_iso(a.get("end_iso") or a["start_iso"])
            except Exception:
                continue
            p = next((p for p in db.get("patients", []) if p.get("id") == a.get("patient_id")), {})
            provider = next((u for u in users if u.get("id") == a.get("doctor_id")), {})
            n = next((u for u in users if u.get("role") == "nurse" and u.get("id") == a.get("nurse_id")), {})
            r = next((r for r in rooms if r.get("id") == a.get("room_id")), {})
            rows.append({
                "When": sdt.strftime("%b %d • %H:%M") + f"–{edt.strftime('%H:%M')}",
                "Patient": p.get("name", f"#{a.get('patient_id')}"),
                "Provider": provider.get("name", f"#{a.get('doctor_id')}"),
                "Nurse": n.get("name", f"#{a.get('nurse_id')}") if a.get("nurse_id") else "—",
                "Room": (r.get('name') or r.get('code') or f"#{a.get('room_id')}") if r else "—",
                "Status": a.get("status", "booked").title(),
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Nothing scheduled in the next week.")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ---------- Calendar (below the lists)
    _render_calendar_section(db)
