# admin_name_ui/doctor_management.py
from __future__ import annotations
from datetime import time
from typing import List, Dict, Any
import json
import re

import streamlit as st
import pandas as pd

# 🔗 read/write doctors.json (data layer)
from admin_name_utils.doctors_io import (
    list_doctors,
    save_doctors,
    upsert_doctor,
)

# ---- availability helpers ----
WEEK_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_TO_IDX = {d: i for i, d in enumerate(WEEK_DAYS)}


def _t(hhmm: str) -> time:
    try:
        hh, mm = (hhmm or "").split(":")
        return time(int(hh), int(mm))
    except Exception:
        return time(0, 0)


def _fmt_time(hhmm: str) -> str:
    t = _t(hhmm)
    return f"{t.hour:02d}:{t.minute:02d}"


def _ensure_slots(slots: Any) -> List[Dict[str, str]]:
    if isinstance(slots, list):
        return [
            {"day": str(r.get("day")), "start": str(r.get("start")), "end": str(r.get("end"))}
            for r in slots
            if isinstance(r, dict) and r.get("day") in WEEK_DAYS
        ]
    if isinstance(slots, str) and slots.strip():
        try:
            parsed = json.loads(slots)
            if isinstance(parsed, list):
                return _ensure_slots(parsed)
        except Exception:
            return []
    return []


def _compress_availability(raw_slots: Any) -> str:
    if isinstance(raw_slots, str):
        s = raw_slots.strip()
        if s and not (s.startswith("[") and s.endswith("]")):
            return s
    slots = _ensure_slots(raw_slots)
    if not slots:
        return "—"

    norm = []
    seen = set()
    for row in slots:
        d = row.get("day")
        if d not in DAY_TO_IDX:
            continue
        start = _fmt_time(row.get("start", "09:00"))
        end = _fmt_time(row.get("end", "17:00"))
        key = (d, start, end)
        if key in seen:
            continue
        seen.add(key)
        norm.append({"day": d, "idx": DAY_TO_IDX[d], "start": start, "end": end})
    norm.sort(key=lambda x: x["idx"])

    parts = []
    i = 0
    while i < len(norm):
        j = i
        s_start, s_end = norm[i]["start"], norm[i]["end"]
        while (
            j + 1 < len(norm)
            and norm[j + 1]["idx"] == norm[j]["idx"] + 1
            and norm[j + 1]["start"] == s_start
            and norm[j + 1]["end"] == s_end
        ):
            j += 1
        a, b = norm[i]["idx"], norm[j]["idx"]
        parts.append(
            f"{WEEK_DAYS[a]} {s_start}–{s_end}"
            if a == b
            else f"{WEEK_DAYS[a]}–{WEEK_DAYS[b]} {s_start}–{s_end}"
        )
        i = j + 1
    return "; ".join(parts) if parts else "—"


# ---- small UI helpers ----
def _card_header(title: str, emoji: str = ""):
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:10px;">
               <div style="font-size:20px">{emoji}</div>
               <h4 style="margin:0;">{title}</h4>
           </div>""",
        unsafe_allow_html=True,
    )


def _badge(text: str, tone: str = "neutral"):
    tones = {
        "neutral": "rgba(255,255,255,.12)",
        "ok": "rgba(34,197,94,.25)",
        "warn": "rgba(234,179,8,.25)",
        "err": "rgba(239,68,68,.25)",
        "info": "rgba(59,130,246,.25)",
    }
    return f"<span style='background:{tones.get(tone, tones['neutral'])};padding:4px 10px;border-radius:999px;font-size:12px;'>{text}</span>"


def _valid_email(s: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s or ""))


def _id_sort_key(doc: Dict[str, Any]):
    """
    Natural sort by trailing number in id (e.g., 'doc12' -> 12), fallback to id string.
    """
    sid = str(doc.get("id") or "")
    m = re.search(r"(\d+)$", sid)
    return (int(m.group(1)) if m else 0, sid.lower())


# ----------------- PAGE -----------------
def render():
    st.markdown(
        "<h3 style='display:flex;align-items:center;gap:10px;margin:0 0 6px 0;'>"
        "🧪 <span>Doctor Management</span></h3>"
        "<p style='margin:0;opacity:.8;'>Manage doctors (ID), specialization, qualifications, and weekly availability.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # 🔍 Load doctors directly from data/doctors.json
    doctors: List[Dict[str, Any]] = list_doctors()

    # ---- Doctors table ----
    doctors_sorted_for_table = sorted(doctors, key=_id_sort_key)

    rows = []
    for u in doctors_sorted_for_table:
        rows.append(
            {
                "ID": u.get("id", ""),  # show JSON id (e.g., doc1)
                "Doctor": u.get("name", ""),
                "Email": u.get("email", ""),
                "Specialization": u.get("specialization", "") or "—",
                "Qualifications": u.get("qualifications", "") or "—",
                "Availability": _compress_availability(u.get("availability", [])),
                "Status": "Deactivated" if u.get("locked") else "Active",
                "Note": u.get("note", "") or "—",
            }
        )

    if rows:
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(
            columns=[
                "ID",
                "Doctor",
                "Email",
                "Specialization",
                "Qualifications",
                "Availability",
                "Status",
                "Note",
            ]
        )

    _card_header("Doctors", "📋")
    st.caption("Sorted by ID.")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ---- Update Doctor (edit details + availability) ----
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    _card_header("Update Doctor", "🛠️")

    if not doctors:
        st.info("No doctors yet.")
        return

    doctors_sorted = sorted(doctors, key=_id_sort_key)
    options = [f"{u.get('id','—')} – {u.get('name','')}" for u in doctors_sorted]
    pick_idx = st.selectbox(
        "Doctor",
        list(range(len(options))),
        format_func=lambda i: options[i],
        key="dm_pick",
        label_visibility="collapsed",
    )
    current = doctors_sorted[pick_idx]

    # Current summary
    st.caption("Current")
    st.markdown(
        f"<div style='border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:10px;'>"
        f"{_badge('ID ' + (str(current.get('id')) or '—'))} "
        f"{_badge('Doctor','info')} "
        f"{_badge('Status: ' + ('Deactivated' if current.get('locked') else 'Active'), 'ok' if not current.get('locked') else 'err')} "
        f"<div style='margin-top:6px'><strong>Availability:</strong> {_compress_availability(current.get('availability', []))}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Editable fields (name, email, specialization, qualifications)
    with st.form(f"dm_profile_{current.get('id','')}"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name", value=current.get("name", ""))
            specialization = st.text_input(
                "Specialization", value=current.get("specialization", "")
            )
        with c2:
            email = st.text_input("Email", value=current.get("email", ""))
            qualifications = st.text_input(
                "Qualifications", value=current.get("qualifications", "")
            )

        # Optional extra fields present in doctors.json
        c3, c4 = st.columns(2)
        with c3:
            license_no = st.text_input("License No.", value=current.get("license_no", ""))
            working_hours = st.text_input(
                "Working Hours", value=current.get("working_hours", "")
            )
        with c4:
            contact = st.text_input("Contact", value=current.get("contact", ""))
            bio = st.text_area("Bio", value=current.get("bio", ""), height=80)

        save_profile = st.form_submit_button("💾 Save Details", type="primary")

    if save_profile:
        errs = []
        if not name.strip():
            errs.append("Name is required.")
        if not email.strip():
            errs.append("Email is required.")
        elif not _valid_email(email):
            errs.append("Email format looks invalid.")
        elif any(
            (u.get("email", "").lower() == email.lower())
            and (u.get("id") != current.get("id"))
            for u in doctors
        ):
            errs.append("Email already exists for another doctor.")
        if errs:
            for e in errs:
                st.error(e)
        else:
            # update the current record (keep any extra fields)
            cur = dict(current)
            cur["name"] = name.strip()
            cur["email"] = email.strip()
            cur["specialization"] = specialization.strip()
            cur["qualifications"] = qualifications.strip()
            cur["license_no"] = license_no.strip()
            cur["working_hours"] = working_hours.strip()
            cur["contact"] = contact.strip()
            cur["bio"] = bio.strip()
            # persist
            upsert_doctor(cur)
            st.success("Details updated.")
            st.rerun()

    # Availability editor
    with st.expander("Edit availability (weekly)", expanded=False):
        ss = st.session_state
        map_key = f"dm_av_{current.get('id')}_map"
        ver_key = f"dm_av_{current.get('id')}_ver"
        initial = _ensure_slots(current.get("availability", []))

        if map_key not in ss:
            valid = {}
            for row in (initial or []):
                d = row.get("day")
                if d in DAY_TO_IDX:
                    valid[d] = {
                        "day": d,
                        "start": row.get("start", "09:00"),
                        "end": row.get("end", "17:00"),
                    }
            ss[map_key] = [valid[d] for d in WEEK_DAYS if d in valid]
        ss.setdefault(ver_key, 0)

        cur_map: List[Dict[str, str]] = ss[map_key]
        cur = {r["day"]: r for r in cur_map}
        ver = ss[ver_key]

        hdr1, hdr2, hdr3, hdr4 = st.columns([0.7, 1.0, 1.0, 1.1])
        with hdr1:
            st.caption("Day")
        with hdr2:
            st.caption("Start")
        with hdr3:
            st.caption("End")
        with hdr4:
            st.caption(" ")

        rows_i = []
        for d in WEEK_DAYS:
            c1, c2, c3, c4 = st.columns([0.7, 1.0, 1.0, 1.1])
            en_key = f"dm_av_{current.get('id')}_v{ver}_en_{d}"
            st_key = f"dm_av_{current.get('id')}_v{ver}_st_{d}"
            et_key = f"dm_av_{current.get('id')}_v{ver}_et_{d}"

            enabled = d in cur
            start_default = _fmt_time(cur.get(d, {}).get("start", "09:00"))
            end_default = _fmt_time(cur.get(d, {}).get("end", "17:00"))

            with c1:
                on = st.checkbox(d, value=enabled, key=en_key)
            with c2:
                s = st.time_input(
                    "Start",
                    key=st_key,
                    value=_t(start_default),
                    step=300,
                    label_visibility="collapsed",
                )
            with c3:
                e = st.time_input(
                    "End",
                    key=et_key,
                    value=_t(end_default),
                    step=300,
                    label_visibility="collapsed",
                )
            with c4:
                pass
            rows_i.append((d, on, s, e))

        cc1, cc2, cc3 = st.columns([1, 1, 2])
        with cc1:
            if st.button(
                "Mon–Fri 09:00–17:00", key=f"dm_av_{current.get('id')}_preset"
            ):
                ss[map_key] = [{"day": d, "start": "09:00", "end": "17:00"} for d in WEEK_DAYS[:5]]
                ss[ver_key] = ver + 1
                st.rerun()
        with cc2:
            if st.button("Clear all", key=f"dm_av_{current.get('id')}_clear"):
                ss[map_key] = []
                ss[ver_key] = ver + 1
                st.rerun()
        with cc3:
            st.caption("Times are local; 24h or AM/PM accepted.")

        slots_new: List[Dict[str, str]] = []
        for d, on, s, e in rows_i:
            if not on:
                continue
            if e <= s:
                st.error(f"{d}: end must be after start.")
                continue
            slots_new.append(
                {
                    "day": d,
                    "start": f"{s.hour:02d}:{s.minute:02d}",
                    "end": f"{e.hour:02d}:{e.minute:02d}",
                }
            )
        ss[map_key] = slots_new

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(
                "Save availability",
                type="primary",
                use_container_width=True,
                key="dm_save_av",
            ):
                cur = dict(current)
                cur["availability"] = slots_new
                upsert_doctor(cur)
                st.success("Availability updated.")
                st.rerun()
        with col2:
            new_state = not bool(current.get("locked"))
            label = "Deactivate doctor" if not current.get("locked") else "Activate doctor"
            if st.button(label, use_container_width=True, key="dm_toggle_active"):
                cur = dict(current)
                cur["locked"] = new_state
                upsert_doctor(cur)
                st.success("Status updated.")
                st.rerun()
