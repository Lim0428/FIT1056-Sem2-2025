# medical_staff/pages/2_💊_MAR.py
import streamlit as st
from components.ui import apply_theme, page_header, card
from components.staff_shared import pick_staff_and_patient
from app.medical_staff_service import MedicalStaffService


st.set_page_config(page_title="Medication (MAR)", page_icon="💊", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Medication Administration Record (MAR)", "Administer & review meds.", "💊")

staff_id, patient = pick_staff_and_patient("mar_pick")
if not patient:
    st.stop()
pid = patient["id"]

with card("Administer medication"):
    c1, c2, c3, c4 = st.columns([2,1,1,1])
    with c1: med = st.text_input("Medication", "", key=f"mar_med_{pid}")
    with c2: dose = st.text_input("Dose", "500 mg", key=f"mar_dose_{pid}")
    with c3: route = st.selectbox("Route", ["PO","IV","IM","SC","PR","SL"], index=0, key=f"mar_route_{pid}")
    with c4: sched = st.text_input("Schedule", "BID", key=f"mar_sched_{pid}")
    given = st.toggle("Given now", value=True, key=f"mar_given_{pid}")
    note = st.text_input("Note (optional)", "", key=f"mar_note_{pid}")
    if st.button("💉 Record administration", type="primary", key=f"mar_add_{pid}"):
        m = svc.add_med_admin(staff_id, pid, med, dose, route, sched, given, note)
        st.success(f"Recorded at {m.timestamp}")

with card("Recent administrations (30 days)"):
    items = svc.list_med_admin(pid, days=30, limit=200)
    if not items: st.caption("No administrations yet.")
    else:
        for m in items:
            tick = "✅" if m["given"] else "⏳"
            st.write(f"{tick} **{m['timestamp']}** — {m['med_name']} {m['dose']} {m['route']} "
                     f"({m['schedule']}) — {m['note']}")
