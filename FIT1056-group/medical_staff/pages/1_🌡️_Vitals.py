# medical_staff/pages/1_🌡️_Vitals.py
from datetime import datetime
import streamlit as st
from components.ui import apply_theme, page_header, card
from components.staff_shared import pick_staff_and_patient
from app.medical_staff import MedicalStaffService

st.set_page_config(page_title="Vitals", page_icon="🌡️", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Vitals", "Capture and view vital signs.", "🌡️")

staff_id, patient = pick_staff_and_patient("vitals_pick")
if not patient:
    st.stop()

pid = patient["id"]

with card("Capture vitals"):
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: temp = st.number_input("Temp (°C)", value=36.8, step=0.1, key=f"v_temp_{pid}")
    with c2: sys  = st.number_input("Systolic", value=120, step=1, key=f"v_sys_{pid}")
    with c3: dia  = st.number_input("Diastolic", value=80, step=1, key=f"v_dia_{pid}")
    with c4: hr   = st.number_input("HR (bpm)", value=72, step=1, key=f"v_hr_{pid}")
    with c5: rr   = st.number_input("RR", value=16, step=1, key=f"v_rr_{pid}")
    with c6: spo2 = st.number_input("SpO₂ (%)", value=98, step=1, key=f"v_spo2_{pid}")
    if st.button("➕ Add vitals", type="primary", key=f"v_add_{pid}"):
        v = svc.add_vitals(staff_id, pid, temp, sys, dia, hr, rr, spo2)
        st.success(f"Recorded at {v.timestamp}")

with card("Recent vitals (30 days)"):
    rows = svc.list_vitals(pid, days=30, limit=200)
    if not rows:
        st.caption("No vitals recorded.")
    else:
        for r in rows:
            st.write(f"• **{r['timestamp']}** — {r['temp_c']}°C, BP {r['systolic']}/{r['diastolic']}, "
                     f"HR {r['hr']}, RR {r['rr']}, SpO₂ {r['spo2']}")
