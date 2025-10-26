# medical_staff/pages/6_📅_Appointments.py
from __future__ import annotations
from datetime import datetime, timedelta, time, date
from typing import List, Dict, Any

import streamlit as st
import pandas as pd

from components.ui import apply_theme, page_header, card
from components.staff_shared import pick_staff_and_patient
from app.medical_staff_service import MedicalStaffService

from app.storage import read_db, write_db, ensure_db

# ---------------- Page setup ----------------
st.set_page_config(page_title="Appointments", page_icon="📅", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Appointments", "Book, reschedule, or cancel.", "📅")

# ---------------- Helpers ----------------
def _now_local() -> datetime:
    return datetime.now()

def _iso_trim_minutes(dt: datetime) -> str:
    """Keep to minute precision (sec, microsec = 0)."""
    return dt.replace(second=0, microsecond=0).isoformat()

def _round_up_to_half_hour(dt: datetime) -> datetime:
    """Next :00 or :30 slot."""
    minute = 0 if dt.minute < 30 else 30
    at_slot = dt.replace(minute=minute, second=0, microsecond=0)
    if at_slot < dt:
        if minute == 0:
            at_slot = at_slot.replace(minute=30)
        else:
            at_slot = (at_slot + timedelta(hours=1)).replace(minute=0)
    return at_slot

def _align_to_half_hour(dt: datetime) -> datetime:
    """Snap to lower :00/:30 boundary for consistent storage."""
    minute = 0 if dt.minute < 30 else 30
    return dt.replace(minute=minute, second=0, microsecond=0)

def _book_appointment(patient_id: str, when_dt: datetime, note: str, who: str) -> Dict[str, Any]:
    """
    Create an appointment in data/carelog.json.
    Writes fields that MedicalStaffService filters on across variants:
      - 'when' (ISO)
      - 'datetime' (ISO; some older code reads this)
      - 'status': 'scheduled'
    """
    ensure_db("data/carelog.json", seed={"patients": [], "appointments": [], "messages": []})
    db = read_db("data/carelog.json")
    appts = db.setdefault("appointments", [])

    appt_id = f"A{int(datetime.now().timestamp() * 1000)}"
    when_iso = _iso_trim_minutes(when_dt)

    entry = {
        "id": appt_id,
        "patient_id": patient_id,
        "when": when_iso,                # ← primary when
        "datetime": when_iso,            # ← compatibility for readers expecting 'datetime'
        "note": note,
        "created_by": who,
        "status": "scheduled",           # ← so filters like status != 'canceled' keep it
    }
    appts.append(entry)
    write_db("data/carelog.json", db)

    # Best-effort audit
    audit_fn = getattr(svc, "_audit", None)
    if callable(audit_fn):
        try:
            audit_fn(who=who, action="appointment.book", target=patient_id, detail=f"{when_iso} | {note}")
        except Exception:
            pass
    return entry

def _load_appts(for_patient: str, now: datetime, window_end: datetime) -> List[Dict[str, Any]]:
    """Use service to fetch; some builds filter by 'when' or 'datetime' transparently."""
    appts = svc.list_appointments(
        for_patient=for_patient,
        from_iso=now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
        to_iso=window_end.isoformat()
    )
    # Fallback sanity: if nothing came back, try reading raw and filtering by ourselves
    if not appts:
        try:
            db = read_db("data/carelog.json")
            raw = db.get("appointments", [])
            out = []
            for a in raw:
                if a.get("patient_id") != for_patient:
                    continue
                iso = a.get("when") or a.get("datetime")
                if not iso:
                    continue
                try:
                    dt = datetime.fromisoformat(iso)
                except Exception:
                    continue
                if now <= dt <= window_end and (a.get("status", "scheduled") != "canceled"):
                    out.append(a)
            appts = sorted(out, key=lambda x: x.get("when", x.get("datetime", "")))
        except Exception:
            pass
    return appts

# ---------------- Pick staff & patient ----------------
staff_id, patient = pick_staff_and_patient("appt_pick")
pid = patient["id"] if patient else None
if not pid:
    st.stop()

now = _now_local()
window_end = now + timedelta(days=90)

# ---------------- TOP: Book appointment ----------------
with card("Book appointment"):
    next_slot = _round_up_to_half_hour(now)

    c1, c2 = st.columns([1, 1])
    with c1:
        book_date: date = st.date_input(
            "Date",
            value=next_slot.date(),
            min_value=now.date(),  # block past days
            key="book_date",
        )
    with c2:
        book_time: time = st.time_input(
            "Time",
            value=time(hour=next_slot.hour, minute=next_slot.minute),
            step=1800,  # 30-minute steps
            key="book_time",
        )

    book_note = st.text_input("Reason / note (optional)", key="book_note")

    a, b = st.columns([1, 3])
    with a:
        if st.button("➕ Book", type="primary", use_container_width=True):
            requested_dt = _align_to_half_hour(datetime.combine(book_date, book_time))
            if requested_dt < _now_local():
                st.error("Cannot book in the past. Please pick a future time.")
            else:
                _book_appointment(pid, requested_dt, book_note.strip(), staff_id or "S001")
                st.success("Appointment booked.")
                st.rerun()
    with b:
        st.caption("Pick a date and time (30-minute steps). Past dates/times are disabled.")

# ---------------- MIDDLE: Two columns (list | edit) ----------------
left, right = st.columns([1.3, 1], gap="large")

# LEFT — Upcoming list
with left:
    with card("Upcoming appointments (next 90 days)"):
        appts: List[Dict[str, Any]] = _load_appts(pid, now=_now_local(), window_end=_now_local() + timedelta(days=90))
        if not appts:
            st.caption("No upcoming appointments in the next 90 days.")
        else:
            rows = []
            for a in appts:
                iso = a.get("when") or a.get("datetime") or ""
                try:
                    when_dt = datetime.fromisoformat(iso)
                    when_disp = when_dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    when_disp = iso
                rows.append({
                    "id": a.get("id", ""),
                    "when": when_disp,
                    "note": a.get("note", ""),
                    "created_by": a.get("created_by", ""),
                })
            df_tbl = pd.DataFrame(rows).sort_values("when", ascending=True)
            st.dataframe(
                df_tbl,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "id": st.column_config.TextColumn("ID", width="small"),
                    "when": st.column_config.DatetimeColumn("When", format="YYYY-MM-DD HH:mm"),
                    "note": st.column_config.TextColumn("Note"),
                    "created_by": st.column_config.TextColumn("Created by", width="small"),
                },
            )

# RIGHT — Edit / Cancel
with right:
    with card("Edit / cancel"):
        appts: List[Dict[str, Any]] = _load_appts(pid, now=_now_local(), window_end=_now_local() + timedelta(days=90))
        if not appts:
            st.caption("Nothing to edit.")
        else:
            # Select appt
            labels = []
            for a in appts:
                iso = a.get("when") or a.get("datetime") or ""
                try:
                    dt = datetime.fromisoformat(iso)
                    labels.append(f"{a.get('id','')} — {dt.strftime('%Y-%m-%d %H:%M')}")
                except Exception:
                    labels.append(f"{a.get('id','')} — {iso}")
            idx = st.selectbox(
                "Select appointment",
                options=list(range(len(appts))),
                format_func=lambda i: labels[i],
                key="appt_select_idx"
            )
            sel = appts[idx]

            # Current time & editors
            iso_cur = sel.get("when") or sel.get("datetime") or ""
            try:
                current_dt = datetime.fromisoformat(iso_cur)
            except Exception:
                current_dt = _round_up_to_half_hour(_now_local())

            c1, c2 = st.columns([1, 1])
            with c1:
                new_date = st.date_input(
                    "New date",
                    value=current_dt.date(),
                    min_value=_now_local().date(),  # no past days
                    key="edit_date",
                )
            with c2:
                default_t = time(hour=current_dt.hour, minute=(0 if current_dt.minute < 30 else 30))
                new_time = st.time_input(
                    "New time",
                    value=default_t,
                    step=1800,  # 30-minute steps
                    key="edit_time",
                )

            edit_note = st.text_input(
                "Reason / note (optional)",
                value=sel.get("note", ""),
                key="edit_note"
            )

            st.divider()
            a1, a2 = st.columns([1, 1])
            with a1:
                if st.button("💾 Save new time", type="primary", use_container_width=True):
                    new_dt = _align_to_half_hour(datetime.combine(new_date, new_time))
                    if new_dt < _now_local():
                        st.error("Cannot reschedule to a past time.")
                    else:
                        # keep both fields in sync
                        iso_new = _iso_trim_minutes(new_dt)
                        svc.reschedule_appointment(sel.get("id"), iso_new, staff_id or "S001")
                        # Optional: also update fallback 'datetime' field so any legacy readers see it
                        try:
                            db = read_db("data/carelog.json")
                            for a in db.get("appointments", []):
                                if a.get("id") == sel.get("id"):
                                    a["when"] = iso_new
                                    a["datetime"] = iso_new
                                    break
                            write_db("data/carelog.json", db)
                        except Exception:
                            pass
                        st.success("Appointment rescheduled.")
                        st.rerun()
            with a2:
                if st.button("🗑️ Cancel appointment", use_container_width=True):
                    svc.cancel_appointment(sel.get("id"), staff_id or "S001")
                    # Optional: mark status canceled in raw store for consistency
                    try:
                        db = read_db("data/carelog.json")
                        for a in db.get("appointments", []):
                            if a.get("id") == sel.get("id"):
                                a["status"] = "canceled"
                                break
                        write_db("data/carelog.json", db)
                    except Exception:
                        pass
                    st.success("Appointment canceled.")
                    st.rerun()

# ---------------- Footnote ----------------
with card():
    st.caption(
        "- On create we now write both **when** and **datetime** plus **status: 'scheduled'** so all readers pick it up.\n"
        "- Book/Reschedule forbid past times and use 30-minute steps.\n"
        "- If you still don’t see new entries, check that **MedicalStaffService** points to `data/carelog.json`."
    )
