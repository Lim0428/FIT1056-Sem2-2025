# admin_name_ui/room_allocation.py
from __future__ import annotations

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

from admin_name_utils.storage import load_db, save_db


# ---------- helpers ----------
def _ensure_db_shapes(db: Dict[str, Any]) -> Dict[str, Any]:
    db.setdefault("rooms", [])
    db.setdefault("patients", [])
    for r in db["rooms"]:
        r.setdefault("id", None)
        r.setdefault("code", "")
        r.setdefault("name", "")
        r.setdefault("type", "")
        r.setdefault("floor", "")
        r.setdefault("capacity", 1)
        r.setdefault("status", "active")
        r.setdefault("equipment", [])
        r.setdefault("note", "")
        r.setdefault("occupied_by", None)
    return db


def _next_room_id(db: Dict[str, Any]) -> int:
    return max([int(r.get("id", 0) or 0) for r in db.get("rooms", [])] + [0]) + 1


def _next_room_code(db: Dict[str, Any]) -> str:
    # Generate RM1, RM2, …
    used = []
    for r in db.get("rooms", []):
        code = str(r.get("code") or "").upper().strip()
        if code.startswith("RM"):
            try:
                used.append(int(code[2:]))
            except Exception:
                pass
    return f"RM{(max(used) + 1) if used else 1}"


def _room_fmt(r: Dict[str, Any]) -> str:
    parts = []
    if r.get("code"):
        parts.append(str(r["code"]))
    if r.get("name"):
        parts.append(str(r["name"]))
    if r.get("type"):
        parts.append(f"({r['type']})")
    return " ".join(parts) or f"Room #{r.get('id','?')}"


def _room_label_with_id(r: Dict[str, Any]) -> str:
    # Always include the ID so selections are unambiguous
    return f"#{r.get('id')} – {_room_fmt(r)}"


def _patient_name(db: Dict[str, Any], pid: int | None) -> str:
    if not pid:
        return "—"
    p = next((x for x in db.get("patients", []) if x.get("id") == pid), None)
    return p.get("name") if p else f"#{pid}"


# ---------- panels ----------
def _panel_add_room(db: Dict[str, Any]):
    rooms: List[Dict[str, Any]] = db.get("rooms", [])
    with st.expander("➕ Add Room", expanded=False):
        with st.form("rr_add"):
            code = st.text_input("Code", value=_next_room_code(db))
            name = st.text_input("Name *", placeholder="e.g., Procedure Room 1")
            typ = st.selectbox(
                "Type",
                [
                    "Consultation", "Procedure", "Operating Theatre", "Recovery",
                    "Imaging", "Ward", "ICU", "Multi-purpose", "Other"
                ],
                index=0,
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                floor = st.text_input("Floor", placeholder="1, 2A")
            with c2:
                capacity = st.number_input("Capacity", min_value=0, max_value=50, value=1, step=1)
            with c3:
                status = st.selectbox("Status", ["Active", "Inactive"], index=0)
            equipment = st.text_input("Equipment / Tags", placeholder="comma separated, e.g., ECG, Ultrasound")
            note = st.text_area("Notes", placeholder="Optional notes")

            if st.form_submit_button("Add Room", type="primary", use_container_width=True):
                if not name.strip():
                    st.error("Name is required.")
                else:
                    new_room = {
                        "id": _next_room_id(db),
                        "code": (code or _next_room_code(db)).upper().strip(),
                        "name": name.strip(),
                        "type": typ,
                        "floor": floor.strip() if floor else "",
                        "capacity": int(capacity),
                        "status": "inactive" if status.lower() == "inactive" else "active",
                        "equipment": [e.strip() for e in (equipment or "").split(",") if e.strip()],
                        "note": note.strip() if note else "",
                        "occupied_by": None,
                        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                    }
                    rooms.append(new_room)
                    db["rooms"] = rooms
                    save_db(db)
                    st.success("Room added.")
                    st.rerun()


def _panel_edit_room(db: Dict[str, Any]):
    rooms: List[Dict[str, Any]] = db.get("rooms", [])
    if not rooms:
        return

    with st.expander("🛠️ Edit Room", expanded=False):
        # Index-based select (stable) + label with ID (unambiguous)
        indices = list(range(len(rooms)))
        sel_idx = st.selectbox(
            "Select a room",
            indices,
            format_func=lambda i: _room_label_with_id(rooms[i]),
            key="rr_edit_pick",
        )
        cur = rooms[sel_idx]

        occ_txt = "Occupied" if cur.get("occupied_by") else "Idle"
        st.caption(f"Status: {occ_txt}  •  Patient: {_patient_name(db, cur.get('occupied_by'))}")

        with st.form(f"rr_edit_{cur.get('id')}"):
            code = st.text_input("Code", value=str(cur.get("code","")))
            name = st.text_input("Name *", value=str(cur.get("name","")))
            type_opts = [
                "Consultation", "Procedure", "Operating Theatre", "Recovery",
                "Imaging", "Ward", "ICU", "Multi-purpose", "Other"
            ]
            idx = type_opts.index(cur.get("type","Consultation")) if cur.get("type") in type_opts else 0
            typ = st.selectbox("Type", type_opts, index=idx)
            c1, c2, c3 = st.columns(3)
            with c1:
                floor = st.text_input("Floor", value=str(cur.get("floor","")))
            with c2:
                capacity = st.number_input("Capacity", min_value=0, max_value=50, value=int(cur.get("capacity",1)), step=1)
            with c3:
                status = st.selectbox("Status", ["Active","Inactive"], index=(0 if str(cur.get("status","active")).lower()!="inactive" else 1))
            equipment = st.text_input("Equipment / Tags", value=", ".join(cur.get("equipment", [])))
            note = st.text_area("Notes", value=str(cur.get("note","")))

            if st.form_submit_button("Save changes", type="primary", use_container_width=True):
                if not name.strip():
                    st.error("Name is required.")
                else:
                    rooms[sel_idx]["code"] = (code or cur.get("code","")).upper().strip()
                    rooms[sel_idx]["name"] = name.strip()
                    rooms[sel_idx]["type"] = typ
                    rooms[sel_idx]["floor"] = floor.strip() if floor else ""
                    rooms[sel_idx]["capacity"] = int(capacity)
                    rooms[sel_idx]["status"] = "inactive" if status.lower()=="inactive" else "active"
                    rooms[sel_idx]["equipment"] = [e.strip() for e in (equipment or "").split(",") if e.strip()]
                    rooms[sel_idx]["note"] = note.strip() if note else ""
                    rooms[sel_idx]["updated_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

                    db["rooms"] = rooms
                    save_db(db)
                    st.success("Room updated.")
                    st.rerun()


# ---------- page ----------
def render():
    db = _ensure_db_shapes(load_db())

    st.markdown("### 🛏️ Rooms & Resources")

    # Rooms table
    st.markdown("#### Rooms")
    if db["rooms"]:
        rows = []
        for r in db["rooms"]:
            rows.append({
                "ID": r.get("id"),
                "Code": r.get("code"),
                "Name": r.get("name"),
                "Type": r.get("type"),
                "Floor": r.get("floor"),
                "Capacity": r.get("capacity"),
                "Status": "Active" if str(r.get("status","active")).lower()!="inactive" else "Inactive",
                "Occupied": _patient_name(db, r.get("occupied_by")),
                "Note": r.get("note",""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=280)
    else:
        st.info("No rooms yet. Add one below.")

    # Add & Edit panels (no delete, no allocate)
    _panel_add_room(db)
    _panel_edit_room(db)
