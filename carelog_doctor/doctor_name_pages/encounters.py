# doctor_name_pages/encounters.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

# read the same files your DataStore uses
from doctor_name_services.data_store import FILES
from doctor_name_services.auth import current_doctor


# ---------------- helpers ----------------
def _read_json(path: Path, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


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


def _when(e: Dict[str, Any]) -> Optional[datetime]:
    """Pick the best timestamp for an encounter."""
    return (
        _parse(e.get("timestamp", "") or e.get("created_at", ""))
        or _parse((e.get("versions") or [{}])[-1].get("timestamp", ""))
    )


def _subtitle(e: Dict[str, Any]) -> str:
    dt = _when(e)
    md = dt.strftime("%b %d, %Y") if dt else "-"
    tpart = _hm(dt) if dt else ""
    patient = e.get("patient_name") or f"Patient #{e.get('patient_id','—')}"
    return f"{patient} • {md} • {tpart}" if tpart else f"{patient} • {md}"


def _title(e: Dict[str, Any]) -> str:
    return (e.get("title") or e.get("type") or "Encounter").strip()


def _etype(e: Dict[str, Any]) -> str:
    return (e.get("type") or "Note").strip()


def _row(enc: Dict[str, Any], idx: int) -> None:
    """Render one encounter card with an Open button."""
    title = _title(enc)
    sub = _subtitle(enc)
    etype = _etype(enc)

    st.markdown(
        f"""
        <div style="
          display:flex; align-items:center; gap:12px; padding:12px;
          background: rgba(255,255,255,0.04);
          border:1px solid rgba(148,163,184,0.28);
          border-radius:14px;">
            <div style="width:40px;height:40px;border-radius:12px;
                        background:#0B1220;border:1px solid rgba(148,163,184,0.35);
                        display:flex;align-items:center;justify-content:center;">📄</div>
            <div style="flex:1 1 auto; min-width:0;">
              <div style="font-weight:800; color:#E7F0FF; font-size:16px;">{title}</div>
              <div style="font-size:12px; color:#A9B7CC; margin-top:2px;">{sub}</div>
              <div style="font-size:11px; color:#7FA8FF; margin-top:6px;">Type: {etype}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "Open",
        key=f"enc_open_{enc.get('id', f'row_{idx}')}",
        type="secondary",
        use_container_width=False,
    ):
        st.session_state["selected_encounter_id"] = enc.get("id")
        st.session_state["nav"] = "Encounters"
        st.session_state["_route_push"] = True
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# -------------- page ---------------------
def page_encounters(store=None):
    """
    Encounters list with:
      • segmented filter by Type (All + unique from data)
      • search within the selected type
      • newest first
      • Open button routes to the Encounters page editor/view
    """
    st.markdown("### Encounters")

    # light polishing
    st.markdown(
        """
        <style>
        .seg-wrap .stRadio > div { gap: 10px; }
        .seg-wrap label { padding: 8px 14px !important; border-radius: 999px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Load encounters safely
    raw = _read_json(FILES["encounters"], [])
    encounters: List[Dict[str, Any]]
    if isinstance(raw, dict) and isinstance(raw.get("encounters"), list):
        encounters = [e for e in raw["encounters"] if isinstance(e, dict)]
    elif isinstance(raw, list):
        encounters = [e for e in raw if isinstance(e, dict)]
    else:
        encounters = []

    # Filter by current doctor when present
    me = current_doctor() or {}
    mid = me.get("id")
    if mid:
        encounters = [e for e in encounters if (e.get("doctor_id") in (None, "", mid) or e.get("doctor_id") == mid)]

    # Build type list
    types = sorted({(_etype(e) or "Note") for e in encounters})
    seg_options = ["All"] + types

    # Controls
    c1, c2 = st.columns([2, 3])
    with c1:
        st.markdown("**Filter**")
        st.markdown('<div class="seg-wrap">', unsafe_allow_html=True)
        pick = st.radio(
            "Type",
            seg_options,
            horizontal=True,
            label_visibility="collapsed",
            key="enc_type_choice",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        q = st.text_input("Search", placeholder="Search by patient, title or note…").strip().lower()

    # Filter according to UI
    rows = encounters[:]
    if pick != "All":
        rows = [e for e in rows if _etype(e).lower() == pick.lower()]

    if q:
        def blob(e: Dict[str, Any]) -> str:
            return " ".join(
                str(x or "")
                for x in [
                    _title(e),
                    _etype(e),
                    e.get("patient_name"),
                    f"Patient {e.get('patient_id','')}",
                    e.get("summary") or e.get("note"),
                ]
            ).lower()
        rows = [e for e in rows if q in blob(e)]

    # newest first
    rows.sort(key=lambda e: _when(e) or datetime.min, reverse=True)

    if not rows:
        st.info("No matching encounters.")
        return

    # Render
    for i, e in enumerate(rows):
        _row(e, i)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
