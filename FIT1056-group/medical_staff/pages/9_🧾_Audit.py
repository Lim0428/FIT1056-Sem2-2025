# medical_staff/pages/9_🧾_Audit.py
import streamlit as st
from components.ui import apply_theme, page_header, card
from components.staff_shared import pick_staff_and_patient
from app.medical_staff import MedicalStaffService

st.set_page_config(page_title="Audit", page_icon="🧾", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Audit", "Recent activity for the selected patient.", "🧾")

staff_id, patient = pick_staff_and_patient("audit_pick")
if not patient:
    st.stop()
pid = patient["id"]

with card("Audit trail"):
    items = svc.list_audit(who=None, patient_id=pid, limit=100)
    if not items: st.caption("No audit entries yet.")
    else:
        for a in items:
            st.write(f"• **{a['when']}** — {a['who']} — {a['action']} — {a['target']} — {a['detail']}")
