# doctor_name_pages/encounters.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from doctor_name_services.data_store import FILES
from doctor_name_services.auth import current_doctor

# -------------------- tiny JSON helpers --------------------
def _read_json(path: Path, default: Any):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _normalize_list(raw, key: str) -> List[dict]:
    if isinstance(raw, dict) and isinstance(raw.get(key), list):
        return [x for x in raw[key] if isinstance(x, dict)]
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []

# -------------------- parsing/format helpers --------------------
def _parse(iso: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(iso).replace("Z", ""))
    except Exception:
        return None

def _hm(dt: datetime) -> str:
    h24, m = dt.hour, dt.minute
    h12 = 12 if (h24 % 12) == 0 else (h24 % 12)
    ampm = "AM" if h24 < 12 else "PM"
    return f"{h12}:{m:02d} {ampm}"

def _date(dt: datetime) -> str:
    return dt.strftime("%b %d, %Y")

def _badge(text: str) -> str:
    return (
        f"<span style='padding:4px 8px;border-radius:999px;"
        f"background:rgba(79,195,247,0.10);color:#BFE9FF;"
        f"border:1px solid rgba(79,195,247,0.25);font-size:12px'>{text}</span>"
    )

# -------------------- data helpers --------------------
def _patient_name_map() -> Dict[str, str]:
    pts = _read_json(FILES["patients"], [])
    out: Dict[str, str] = {}
    for p in (pts if isinstance(pts, list) else []):
        pid = p.get("id")
        if pid:
            out[pid] = p.get("name") or f"Patient {pid}"
    return out

def _encounters_for_me() -> List[Dict[str, Any]]:
    me = current_doctor() or {}
    me_id = me.get("id")
    encs_raw = _read_json(FILES["encounters"], [])
    encs = _normalize_list(encs_raw, "encounters")
    # Keep those authored/owned by this doctor if doctor_id present; otherwise keep all
    rows = []
    for e in encs:
        if me_id and e.get("doctor_id") and e.get("doctor_id") != me_id:
            continue
        rows.append(e)
    # newest first
    rows.sort(
        key=lambda e: (
            _parse(e.get("timestamp", "") or e.get("created_at", ""))
            or _parse((e.get("versions") or [{}])[-1].get("timestamp", ""))
            or datetime.min
        ),
        reverse=True,
    )
    return rows

# -------------------- UI row --------------------
def _enc_row(e: Dict[str, Any], idx: int, name_map: Dict[str, str]) -> None:
    title = e.get("title") or e.get("type") or "Encounter"
    pid = e.get("patient_id", "—")
    pname = name_map.get(pid, f"Patient #{pid}")
    when = (
        _parse(e.get("timestamp", "") or e.get("created_at", ""))
        or _parse((e.get("versions") or [{}])[-1].get("timestamp", ""))
    )
    subtitle = _date(when) + " • " + _hm(when) if when else "—"

    typ = (e.get("type") or "").title()
    status = (e.get("status") or "Open").title()

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:12px; padding:12px;
                    border-bottom:1px solid rgba(148,163,184,0.30);">
          <div style="width:38px;height:38px;border-radius:10px;
                      background:#0B1220;
                      border:1px solid rgba(148,163,184,0.35);
                      display:flex;align-items:center;justify-content:center;">🗒️</div>
          <div style="flex:1 1 auto; min-width:0;">
            <div style="font-weight:700; color:#E5E7EB;">{title}</div>
            <div style="font-size:12px; color:#CBD5E1; margin-top:2px;">{pname} • {subtitle}</div>
            <div style="margin-top:6px;">{_badge(typ or 'Encounter')} {_badge(status)}</div>
          </div>
          <div style="margin-left:auto;">
        """,
        unsafe_allow_html=True,
    )

    open_btn = st.button("Open", key=f"enc_open_{e.get('id', idx)}", type="secondary")
    st.markdown("</div></div>", unsafe_allow_html=True)

    if open_btn:
        # Store selected encounter in session; your Encounters detail page
        # could consume this or you can show inline details here.
        st.session_state["selected_encounter_id"] = e.get("id")
        # Inline details (quick view):
        with st.expander("Details", expanded=True):
            st.json({
                "id": e.get("id"),
                "patient_id": e.get("patient_id"),
                "type": e.get("type"),
                "status": e.get("status"),
                "timestamp": e.get("timestamp") or e.get("created_at"),
                "summary": e.get("summary") or "",
                "versions": e.get("versions") or [],
            })

# -------------------- PAGE --------------------
def page_encounters(store=None):
    st.markdown("### Encounters")

    # Filters
    left, right = st.columns([3, 5])
    with left:
        cat = st.radio(
            "Type",
            ["All", "Consultation", "First Visit", "Follow-up"],
            horizontal=True,
            index=0,
            key="enc_type_filter",
        )
    with right:
        q = st.text_input("Search (patient / title / summary)", placeholder="Type to filter…").strip().lower()

    name_map = _patient_name_map()
    rows = _encounters_for_me()

    # Apply category filter
    if cat != "All":
        rows = [e for e in rows if (e.get("type") or "").strip().lower() == cat.lower()]

    # Apply search
    if q:
        def blob(e: Dict[str, Any]) -> str:
            return " ".join([
                name_map.get(e.get("patient_id",""), ""),
                str(e.get("title","")),
                str(e.get("type","")),
                str(e.get("summary","")),
            ]).lower()
        rows = [e for e in rows if q in blob(e)]

    if not rows:
        st.info("No encounters match your filters.")
        return

    # List
    for i, e in enumerate(rows):
        _enc_row(e, i, name_map)
