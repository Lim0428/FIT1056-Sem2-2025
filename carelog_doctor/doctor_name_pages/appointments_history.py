# doctor_name_pages/appointments_history.py
from __future__ import annotations
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional

# ---------------- helpers ----------------
def _parse(iso: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(iso).replace("Z", ""))
    except Exception:
        return None

def _hm(dt: datetime, include_ampm: bool = True) -> str:
    """Windows-safe hour:min formatter (no %-I)."""
    h24, m = dt.hour, dt.minute
    h12 = 12 if (h24 % 12) == 0 else (h24 % 12)
    ampm = "AM" if h24 < 12 else "PM"
    core = f"{h12}" if m == 0 else f"{h12}:{m:02d}"
    return f"{core} {ampm}" if include_ampm else core

def _fmt_range(a: Dict[str, Any]) -> str:
    s = _parse(a.get("start", ""))
    e = _parse(a.get("end", ""))
    if not s:
        return "-"
    md = s.strftime("%b %d, %Y")
    if e:
        same_ampm = ("AM" if s.hour < 12 else "PM") == ("AM" if e.hour < 12 else "PM")
        if same_ampm:
            return f"{md} • {_hm(s, include_ampm=False)}–{_hm(e)}"
        return f"{md} • {_hm(s)}–{_hm(e)}"
    return f"{md} • {_hm(s)}"

def _reason(a: Dict[str, Any]) -> str:
    return (a.get("reason") or "").strip() or "Consultation"

def _patient(a: Dict[str, Any]) -> str:
    return a.get("patient_name") or f"Patient #{a.get('patient_id','—')}"

def _is_past(a: Dict[str, Any], now: datetime) -> bool:
    dt = _parse(a.get("start", ""))
    return bool(dt and dt < now)

# -------------- row card -----------------
def _history_row(appt: Dict[str, Any], idx: int) -> None:
    title = _reason(appt)
    subtitle = f"{_patient(appt)} • {_fmt_range(appt)}"

    st.markdown(
        f"""
        <div style="
          display:flex; align-items:center; gap:12px; padding:12px;
          background: rgba(255,255,255,0.04);
          border:1px solid rgba(148,163,184,0.28);
          border-radius:14px;">
            <div style="width:40px;height:40px;border-radius:12px;
                        background:#0B1220;border:1px solid rgba(148,163,184,0.35);
                        display:flex;align-items:center;justify-content:center;">📌</div>
            <div style="flex:1 1 auto; min-width:0;">
              <div style="font-weight:800; color:#E7F0FF; font-size:16px;">{title}</div>
              <div style="font-size:12px; color:#A9B7CC; margin-top:2px;">{subtitle}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # actions (right-aligned) rendered as a real Streamlit button
    col_open = st.columns([1])[0]
    open_btn = col_open.button("Open", key=f"hist_open_{appt.get('id', f'row_{idx}')}", type="secondary")
    st.markdown("</div>", unsafe_allow_html=True)

    if open_btn:
        st.session_state["selected_appt_id"] = appt.get("id")
        st.session_state["nav"] = "Appointments"
        st.session_state["_route_push"] = True
        st.rerun()

# -------------- page ---------------------
def page_appointments_history(store):
    st.markdown("### Appointments History")

    # Minimal styling for cards and selector
    st.markdown(
        """
        <style>
        .seg-wrap .stRadio > div { gap: 10px; }
        .seg-wrap label { padding: 8px 14px !important; border-radius: 999px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Controls row
    with st.container():
        c1, c2 = st.columns([2, 3])
        with c1:
            st.markdown("**Filter**")
            with st.container():
                st.markdown('<div class="seg-wrap">', unsafe_allow_html=True)
                choice = st.radio(
                    "Type",
                    ["All", "First Visit", "Consultation"],
                    horizontal=True,
                    index=0,
                    label_visibility="collapsed",
                    key="hist_type_choice",
                )
                st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            q = st.text_input("Search", placeholder="Search by patient or note…").strip().lower()

    # Load and shape data
    appts: List[Dict[str, Any]] = store.list_all_appointments() or []
    now = datetime.now()

    # History only (past)
    rows = [a for a in appts if _is_past(a, now)]

    # Category filter
    if choice != "All":
        wanted = choice.lower()
        rows = [a for a in rows if _reason(a).lower() == wanted]

    # Search within the category
    if q:
        rows = [
            a
            for a in rows
            if (q in _patient(a).lower())
            or (q in _reason(a).lower())
            or (q in (_fmt_range(a).lower()))
        ]

    # newest first
    rows.sort(key=lambda x: _parse(x.get("start", "")) or datetime.min, reverse=True)

    # Empty state
    if not rows:
        st.info("No matching appointments.")
        return

    # Render list
    for i, a in enumerate(rows):
        _history_row(a, i)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
