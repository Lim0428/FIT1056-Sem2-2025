# doctor_name_pages/appointments_history.py
from __future__ import annotations
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional

def _parse(iso: str) -> Optional[datetime]:
    try: return datetime.fromisoformat(str(iso).replace("Z", ""))
    except: return None

def _hm(dt: datetime, include_ampm: bool = True) -> str:
    h24, m = dt.hour, dt.minute
    h12 = 12 if (h24 % 12) == 0 else (h24 % 12)
    ampm = "AM" if h24 < 12 else "PM"
    core = f"{h12}" if m == 0 else f"{h12}:{m:02d}"
    return f"{core} {ampm}" if include_ampm else core

def _fmt_range(a: dict) -> str:
    s = _parse(a.get("start", "")); e = _parse(a.get("end", ""))
    if not s: return "-"
    md = s.strftime("%b %d, %Y")
    if e:
        same_ampm = ("AM" if s.hour < 12 else "PM") == ("AM" if e.hour < 12 else "PM")
        if same_ampm: return f"{md} • {_hm(s, include_ampm=False)}–{_hm(e)}"
        return f"{md} • {_hm(s)}–{_hm(e)}"
    return f"{md} • {_hm(s)}"

def _row(appt: Dict[str, Any], idx: int) -> None:
    title = appt.get("reason", "Consultation") or "Consultation"
    subtitle = _fmt_range(appt)
    patient = appt.get("patient_name") or f"Patient #{appt.get('patient_id','—')}"
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:12px; padding:12px;
                    border-bottom:1px solid rgba(148,163,184,0.30);">
          <div style="width:38px;height:38px;border-radius:10px;
                      background:#0B1220; border:1px solid rgba(148,163,184,0.35);
                      display:flex;align-items:center;justify-content:center;">📌</div>
          <div style="flex:1 1 auto; min-width:0;">
            <div style="font-weight:700; color:#E5E7EB;">{title}</div>
            <div style="font-size:12px; color:#CBD5E1; margin-top:2px;">{patient} • {subtitle}</div>
          </div>
          <div style="margin-left:auto;">
        """,
        unsafe_allow_html=True,
    )
    safe_id = str(appt.get("id") or "row")
    if st.button("Open", key=f"hist_open_{safe_id}_{idx}", type="secondary"):
        st.session_state["selected_appt_id"] = appt.get("id")
        st.session_state["nav"] = "Appointments"
        st.session_state["_route_push"] = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def page_appointments_history(store):
    st.markdown("### Appointments History")
    scope = st.radio("Scope", ["This month", "All past"], horizontal=True, index=0)
    c1, c2, c3 = st.columns([2,2,3])
    with c1: start_d = st.date_input("Start date", value=None)
    with c2: end_d   = st.date_input("End date", value=None)
    with c3: q = st.text_input("Search (patient / reason)", placeholder="Type to filter…").strip().lower()

    appts: List[Dict[str, Any]] = store.list_all_appointments() or []
    now = datetime.now()
    rows: List[Dict[str, Any]] = []
    for a in appts:
        dt = _parse(a.get("start", ""))
        if not dt or dt >= now: continue
        if scope == "This month" and not (dt.year == now.year and dt.month == now.month): continue
        if start_d and dt.date() < start_d: continue
        if end_d and dt.date() > end_d: continue
        blob = f"{a.get('patient_name','')} {a.get('reason','')}".lower()
        if q and q not in blob: continue
        rows.append(a)
    rows.sort(key=lambda x: _parse(x.get("start","")) or datetime.min, reverse=True)

    if not rows:
        st.info("No matching historical appointments."); return
    for i,a in enumerate(rows): _row(a,i)
