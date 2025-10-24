# doctor_name_pages/patient.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
from doctor_name_services.data_store import FILES
from doctor_name_services.auth import current_doctor

# ----------------------------- utils -----------------------------
def _read_json(path: Path, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _write_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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

def _bold(s: str) -> str:
    return f"<span style='font-weight:800'>{s}</span>"

def _divider(px: int = 10):
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)

# ----------------------------- data helpers -----------------------------
def _load_patients_for_me() -> List[Dict[str, Any]]:
    me = current_doctor() or {}
    me_id = me.get("id")
    pts = [p for p in _read_json(FILES["patients"], []) if isinstance(p, dict)]
    if not me_id:
        return pts
    return [
        p
        for p in pts
        if (me_id in p.get("assigned_doctor_ids", []))
        or p.get("consent_to_all_doctors", False)
    ]

def _get_patient(pid: str) -> Optional[Dict[str, Any]]:
    for p in _load_patients_for_me():
        if p.get("id") == pid:
            return p
    return None

def _save_patient(updated: Dict[str, Any]) -> None:
    """Write back to patients.json by replacing the matching id."""
    pts = _read_json(FILES["patients"], [])
    for i, p in enumerate(pts):
        if isinstance(p, dict) and p.get("id") == updated.get("id"):
            pts[i] = updated
            break
    _write_json(FILES["patients"], pts)

def _appointments_for_patient(pid: str) -> List[Dict[str, Any]]:
    appts = _read_json(FILES["appointments"], [])
    if isinstance(appts, dict) and isinstance(appts.get("appointments"), list):
        appts = appts["appointments"]
    rows = [a for a in appts if isinstance(a, dict) and a.get("patient_id") == pid]
    rows.sort(key=lambda a: _parse(a.get("start", "")) or datetime.min, reverse=True)
    return rows

def _encounters_for_patient(pid: str) -> List[Dict[str, Any]]:
    encs = _read_json(FILES["encounters"], [])
    if isinstance(encs, dict) and isinstance(encs.get("encounters"), list):
        encs = encs["encounters"]
    rows = [e for e in encs if isinstance(e, dict) and e.get("patient_id") == pid]

    def _when(e):
        return (
            _parse(e.get("timestamp", "") or e.get("created_at", ""))
            or _parse((e.get("versions") or [{}])[-1].get("timestamp", ""))
        )

    rows.sort(key=lambda e: _when(e) or datetime.min, reverse=True)
    return rows

# ----------------------------- UI atoms -----------------------------
def _avatar_circle(emoji: str = "🧑", bg="#0D1422") -> str:
    return (
        f"<div style='width:56px;height:56px;border-radius:50%;"
        f"background:{bg};display:flex;align-items:center;justify-content:center;"
        f"font-size:26px;border:1px solid rgba(148,163,184,0.35);'>{emoji}</div>"
    )

def _chip(text: str) -> str:
    return (
        f"<span style='padding:6px 10px;border-radius:999px;"
        f"background:rgba(79,195,247,0.10);color:#BFE9FF;"
        f"border:1px solid rgba(79,195,247,0.25);font-size:12px'>{text}</span>"
    )

def _metric_box(value: str, label: str) -> str:
    return (
        "<div style='flex:1 1 0; background:rgba(255,255,255,0.04);"
        "border:1px solid rgba(148,163,184,0.28); border-radius:12px; padding:10px; text-align:center;'>"
        f"<div style='font-size:20px;font-weight:800'>{value}</div>"
        f"<div style='font-size:12px;color:#A9B7CC'>{label}</div>"
        "</div>"
    )

def _patient_row(p: Dict[str, Any], i: int) -> bool:
    """Left list row (returns True if clicked)."""
    st.markdown(
        """
        <style>
        .pt-list .stButton > button {
            width: 100%;
            text-align: left;
            white-space: pre-line;
            line-height: 1.15;
            background:#0D1422;
            border:1px solid rgba(148,163,184,0.28);
            color:#E5E7EB;
            padding:12px 14px;
            border-radius:12px;
        }
        .pt-list .stButton > button:hover { background:#121B2C; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    name = p.get("name", "Patient")
    contact = p.get("contact", "—")
    tag = ", ".join(map(str, p.get("conditions", [])[:2])) or "—"
    label = f"{name}\n{contact}\n{tag}"
    return st.button(label, key=f"pt_row_{p.get('id','x')}_{i}")

def _card_header(p: Dict[str, Any]) -> None:
    name = p.get("name", "Unknown")
    contact = p.get("contact", "—")
    chips = []
    if p.get("consent_to_all_doctors"):
        chips.append("Consented")
    if p.get("allergies"):
        chips.append(f"Allergies {len(p['allergies'])}")
    if p.get("conditions"):
        chips.append(f"Conditions {len(p['conditions'])}")
    chips_html = " ".join(_chip(c) for c in chips)

    st.markdown(
        f"""
        <div style="display:flex; gap:14px; align-items:center;">
          {_avatar_circle('🧑')}
          <div style="flex:1 1 auto;">
            <div style="font-weight:800;font-size:20px;color:#E7F0FF">{name}</div>
            <div style="font-size:12px;color:#A9B7CC; margin-top:2px">{contact}</div>
            <div style="margin-top:8px">{chips_html}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------- COM-CARD -----------------------------
def _patient_comcard(p: Dict[str, Any]):
    """Full “com-card” with clearer tabs and prescription versioning."""
    # — Make tabs clearer/brighter —
    st.markdown(
        """
        <style>
        .stTabs [role="tab"] {
            color:#DCEBFF !important;
            font-weight:600;
            padding:8px 14px;
        }
        .stTabs [role="tab"][aria-selected="true"] {
            color:#FFFFFF !important;
            border-bottom:2px solid #ff5c5c !important;
            background:rgba(255,255,255,0.04);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        _card_header(p)
        _divider()

        appts = _appointments_for_patient(p["id"])
        encs  = _encounters_for_patient(p["id"])

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                _metric_box(str(len(p.get("conditions", []))), "Conditions"),
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(_metric_box(str(len(encs)), "Encounters"), unsafe_allow_html=True)
        with c3:
            st.markdown(_metric_box(str(len(appts)), "Appointments"), unsafe_allow_html=True)

        _divider()

        tabs = st.tabs(["Overview", "Medical record", "Visits", "Encounters", "Files"])

        # ------------ Overview ------------
        with tabs[0]:
            colA, colB = st.columns(2)
            with colA:
                st.markdown(_bold("Contact"), unsafe_allow_html=True)
                st.write(p.get("contact", "—"))
                st.markdown(_bold("Consent"), unsafe_allow_html=True)
                st.write(
                    "Consented to all doctors"
                    if p.get("consent_to_all_doctors")
                    else "Assigned only"
                )
            with colB:
                st.markdown(_bold("Allergies"), unsafe_allow_html=True)
                st.write(", ".join(p.get("allergies", [])) or "—")
                st.markdown(_bold("Current Medications"), unsafe_allow_html=True)
                st.write(", ".join(p.get("medications", [])) or "—")

        # ------------ Medical Record + Prescribe (versioned) ------------
        with tabs[1]:
            st.markdown("### Medical record")

            # 1) Prescribe FIRST -> then render list so it appears immediately.
            with st.expander("➕ Prescribe treatment", expanded=False):
                with st.form(key=f"rx_form_{p['id']}", clear_on_submit=True):
                    st.caption(
                        "Add one item and save to create a new version (you can add more later)."
                    )

                    c1, c2 = st.columns([3, 2])
                    with c1:
                        drug = st.text_input(
                            "Medication",
                            placeholder="e.g., Amlodipine 5 mg",
                            key=f"rx_drug_{p['id']}",
                        )
                        dose = st.text_input(
                            "Dose", placeholder="e.g., 5 mg", key=f"rx_dose_{p['id']}"
                        )
                        freq = st.text_input(
                            "Frequency",
                            placeholder="e.g., OD / BID / TDS",
                            key=f"rx_freq_{p['id']}",
                        )
                    with c2:
                        duration = st.text_input(
                            "Duration",
                            placeholder="e.g., 14 days",
                            key=f"rx_dur_{p['id']}",
                        )
                        notes = st.text_area(
                            "Notes",
                            placeholder="Any extra instruction",
                            key=f"rx_notes_{p['id']}",
                        )

                    save_rx = st.form_submit_button(
                        "Save prescription", use_container_width=True
                    )

                    if save_rx:
                        if not (drug or "").strip():
                            st.warning("Medication name is required.")
                        else:
                            me = current_doctor() or {}
                            new_entry = {
                                "timestamp": datetime.now().isoformat(),
                                "author": {
                                    "id": me.get("id"),
                                    "name": me.get("email") or "Doctor",
                                },
                                "items": [
                                    {
                                        "drug": drug.strip(),
                                        "dose": (dose or "").strip() or None,
                                        "frequency": (freq or "").strip() or None,
                                        "duration": (duration or "").strip() or None,
                                    }
                                ],
                                "notes": (notes or "").strip() or None,
                            }

                            # Append (versioning), don't overwrite
                            treatments = list(p.get("treatments", []))
                            treatments.append(new_entry)
                            p["treatments"] = treatments  # update in-memory so it renders now
                            _save_patient(p)              # persist to disk

                            st.toast("Prescription saved ✅", icon="✅")

            # 2) Then render Conditions/History + Treatment list
            st.markdown(_bold("Conditions"), unsafe_allow_html=True)
            if p.get("conditions"):
                for c in p["conditions"]:
                    st.markdown(f"- {c}")
            else:
                st.caption("No chronic conditions recorded.")
            _divider(8)

            st.markdown(_bold("History"), unsafe_allow_html=True)
            if p.get("history"):
                for h in p["history"]:
                    st.markdown(f"- {h}")
            else:
                st.caption("No past history recorded.")
            _divider(12)

            st.markdown("### Treatment plan (versioned)")
            treatments: List[Dict[str, Any]] = p.get("treatments", [])
            if not treatments:
                st.caption("No treatment prescribed yet.")
            else:
                for t in reversed(treatments):  # newest first
                    ts = _parse(t.get("timestamp", "")) or datetime.min
                    author = t.get("author", {})
                    who = author.get("name") or author.get("id") or "Unknown"
                    header = f"{_date(ts)} • {_hm(ts)} • by {who}"
                    with st.container(border=True):
                        st.markdown(f"**{header}**")
                        meds = t.get("items", [])
                        if meds:
                            for m in meds:
                                line = f"- {m.get('drug','(drug)')}"
                                if m.get("dose"):
                                    line += f", {m['dose']}"
                                if m.get("frequency"):
                                    line += f", {m['frequency']}"
                                if m.get("duration"):
                                    line += f", {m['duration']}"
                                st.markdown(line)
                        if t.get("notes"):
                            st.caption(t["notes"])

        # ------------ Visits ------------
        with tabs[2]:
            appts = _appointments_for_patient(p["id"])
            if not appts:
                st.caption("No appointments.")
            else:
                for a in appts:
                    s = _parse(a.get("start", ""))
                    e = _parse(a.get("end", ""))
                    line = f"{_date(s)} • {_hm(s)}"
                    if e:
                        line += f" – {_hm(e)}"
                    reason = (a.get("reason") or "Consultation").title()
                    with st.container(border=True):
                        st.markdown(f"**{reason}**")
                        st.caption(line)
                        if st.button(
                            "Open",
                            key=f"pt_open_appt_{a.get('id', id(a))}",
                            type="secondary",
                        ):
                            st.session_state["selected_appt_id"] = a.get("id")
                            st.session_state["nav"] = "Appointments"
                            st.session_state["_route_push"] = True
                            st.rerun()

        # ------------ Encounters ------------
        with tabs[3]:
            encs = _encounters_for_patient(p["id"])
            if not encs:
                st.caption("No encounters.")
            else:
                for e in encs:
                    when = (
                        _parse(e.get("timestamp", "") or e.get("created_at", ""))
                        or _parse((e.get("versions") or [{}])[-1].get("timestamp", ""))
                    )
                    title = e.get("title") or e.get("type") or "Encounter"
                    with st.container(border=True):
                        st.markdown(f"**{title}**")
                        st.caption(_date(when) if when else "—")
                        if st.button(
                            "Open",
                            key=f"pt_open_enc_{e.get('id', id(e))}",
                            type="secondary",
                        ):
                            st.session_state["selected_encounter_id"] = e.get("id")
                            st.session_state["nav"] = "Encounters"
                            st.session_state["_route_push"] = True
                            st.rerun()

        # ------------ Files ------------
        with tabs[4]:
            files = p.get("uploads") or []
            if not files:
                st.caption("No uploaded files.")
            else:
                for f in files:
                    with st.container(border=True):
                        st.write(f)

# ----------------------------- page (two states) -----------------------------
def page_patients(store=None):
    """
    Two-state Patients page:
      • LIST mode: search + list (left), preview card (right)
      • DETAIL mode: only the full com-card + 'Back to patient list' button
    """
    st.markdown("### Patients")

    if "patients_mode" not in st.session_state:
        st.session_state["patients_mode"] = "list"
    if "selected_patient_id" not in st.session_state:
        pts0 = _load_patients_for_me()
        st.session_state["selected_patient_id"] = pts0[0]["id"] if pts0 else None

    mode = st.session_state["patients_mode"]

    # ---------- DETAIL MODE ----------
    if mode == "detail":
        pid = st.session_state.get("selected_patient_id")
        p = _get_patient(pid) if pid else None
        if not p:
            st.info("No patient selected. Returning to list.")
            st.session_state["patients_mode"] = "list"
            st.rerun()

        _patient_comcard(p)
        _divider(12)

        # back button
        st.markdown(
            """
            <style>
            .backwrap .stButton > button {
                background:transparent; color:#BFE9FF; border-width:1.5px;
                border-style:solid; border-image:linear-gradient(90deg,#4FC3F7,#2E5AAC) 1;
                border-radius:14px; padding:.6rem 1.1rem;
            }
            .backwrap .stButton > button:hover { background:rgba(79,195,247,.08); }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="backwrap">', unsafe_allow_html=True)
        if st.button("← Back to patient list", key="pt_back_to_list"):
            st.session_state["patients_mode"] = "list"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- LIST MODE ----------
    left, right = st.columns([5, 7], gap="large")

    with left:
        st.markdown("**Your Patients**")
        q = st.text_input(
            "Search", placeholder="Search by name, contact or condition…"
        ).strip().lower()

        pts = _load_patients_for_me()
        if q:
            def blob(p):
                return " ".join(
                    [
                        p.get("name", ""),
                        p.get("contact", ""),
                        " ".join(p.get("conditions", [])),
                        " ".join(p.get("allergies", [])),
                    ]
                ).lower()

            pts = [p for p in pts if q in blob(p)]

        if not pts:
            st.info("No matching patients.")
        else:
            st.markdown('<div class="pt-list">', unsafe_allow_html=True)
            for i, p in enumerate(pts):
                if _patient_row(p, i):
                    st.session_state["selected_patient_id"] = p.get("id")
                    st.session_state["patients_mode"] = "detail"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    with right:
        pid = st.session_state.get("selected_patient_id")
        p = _get_patient(pid) if pid else (pts[0] if "pts" in locals() and pts else None)
        if not p:
            st.info("Select a patient to view details.")
            return
        _patient_comcard(p)
