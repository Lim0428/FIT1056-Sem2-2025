# medical_staff/components/staff_shared.py
from __future__ import annotations
import streamlit as st
from components.ui import card
from app.medical_staff import MedicalStaffService

_svc = MedicalStaffService()

def pick_staff_and_patient(key_prefix: str = "pick"):
    """
    Renders a small 'Find Patient' block and returns (staff_id, patient_dict)
    or (None, None) if not selected.
    """
    with card("Find Patient"):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            q = st.text_input(
                "Search by name / ID / contact", "",
                key=f"{key_prefix}_q",
                placeholder="e.g. P0001, Alice, +60..."
            )
        with c2:
            assigned_only = st.toggle("Only my patients", value=False, key=f"{key_prefix}_assigned")
        with c3:
            staff_id = st.text_input(
                "Staff ID (for audit)",
                value=st.session_state.get("auth_user", "S001"),
                key=f"{key_prefix}_staff"
            )

        patients = _svc.search_patients(q, assigned_to=(staff_id if assigned_only else None))
        if not patients:
            st.caption("No matching patients. Add patients in data/carelog.json.")
            return staff_id, None

        names = [f"{p.get('name','(no name)')} — {p.get('id','')}" for p in patients]
        idx = st.selectbox("Select patient", options=list(range(len(names))),
                           format_func=lambda i: names[i], key=f"{key_prefix}_sel")
        patient = patients[idx]
        return staff_id, patient
