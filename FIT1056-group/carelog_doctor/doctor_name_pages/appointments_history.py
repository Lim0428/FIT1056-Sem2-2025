# doctor_name_pages/appointments_history.py
from __future__ import annotations
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional

# ---------- tiny helpers ----------
def _parse(iso: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(iso).replace("Z", ""))
    except Exception:
        return None

def _hm(dt: datetime, include_ampm: bool = True) -> str:
    h24, m = dt.hour, dt.minute
    h12 = 12 if (h24 % 12) == 0 else (h24 % 12)
    ampm = "AM" if h24 < 12 else "PM"
    core = f"{h12}" if m == 0 else f"{h12}:{m:02d}"
    return f"{core} {ampm}" if include_ampm else core

def _fmt_range(a: dict) -> str:
    s = _parse(a.get("start", "")); e = _parse(a.get("end", ""))
    if not s:
        return "-"
    md = s.strftime("%b %d, %Y")
    if e:
        same_ampm = ("AM" if s.hour < 12 else "PM") == ("AM" if e.hour < 12 else "PM")
        if same_ampm:
            return f"{md} • {_hm(s, include_ampm=False)}–{_hm(e)}"
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
                      background:#0B1220;
                      border:1px solid rgba(148,163,184,0.35);
                      display:flex;align-items:center;justify-content:center;">📌</div>
          <div style="flex:1 1 auto; min-width:0;">
            <div style="font-weight:700; color:#E5E7EB;">{title}</div>
            <div style="font-size:12px; color:#CBD5E1; margin-top:2px;">{patient} • {subtitle}</div>
          </div>
          <div style="margin-left:auto;">
        """,
        unsafe_allow_html=True,
    )
    # unique button key by id+idx
    safe_id = str(appt.get("id") or "row")
    if st.button("Open", key=f"hist_open_{safe_id}_{idx}", type="secondary"):
        st.session_state["selected_appt_id"] = appt.get("id")
        st.session_state["nav"] = "Appointments"
        st.session_state["_route_push"] = True
        st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)

# ---------- page ----------
def page_appointments_history(store):
    # top action bar with back button
    st.markdown(
        """
        <style>
        .ah-actions { display:flex; justify-content:space-between; align-items:center; gap:8px; }
        .ah-back .stButton > button{
            background:transparent !important; color:#E6F4FF !important;
            border-width:1.5px !important; border-style:solid !important;
            border-radius:14px !important; padding:.45rem 0.9rem !important;
            border-image: linear-gradient(90deg, #4FC3F7 0%, #2E5AAC 100%) 1 !important;
            box-shadow:none !important;
        }
        .ah-back .stButton > button:hover{
            box-shadow:0 0 0 3px rgba(79,195,247,0.12) inset,
                       0 6px 24px rgba(46,90,172,0.25) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    colL, colR = st.columns([1, 3])
    with colL:
        st.markdown('<div class="ah-back">', unsafe_allow_html=True)
        if st.button("← Back to dashboard", key="ah_back_to_dash"):
            st.session_state["nav"] = "Dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with colR:
        st.markdown("### Appointments History")

    # filters
    scope = st.radio("Scope", ["This month", "All past"], horizontal=True, index=0)
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        start_d = st.date_input("Start date", value=None)
    with col2:
        end_d = st.date_input("End date", value=None)
    with col3:
        q = st.text_input("Search (patient / reason)", placeholder="Type to filter…").strip().lower()

    # data
    appts: List[Dict[str, Any]] = store.list_all_appointments() or []
    now = datetime.now()

    rows: List[Dict[str, Any]] = []
    for a in appts:
        dt = _parse(a.get("start", ""))
        if not dt or dt >= now:
            continue  # history = past only

        if scope == "This month" and not (dt.year == now.year and dt.month == now.month):
            continue

        if start_d and dt.date() < start_d:
            continue
        if end_d and dt.date() > end_d:
            continue

        blob = f"{a.get('patient_name','')} {a.get('reason','')}".lower()
        if q and q not in blob:
            continue

        rows.append(a)

    rows.sort(key=lambda x: _parse(x.get("start","")) or datetime.min, reverse=True)

    if not rows:
        st.info("No matching historical appointments.")
        return

    for i, a in enumerate(rows):
        _row(a, i)
