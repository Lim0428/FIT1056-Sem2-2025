# medical_staff/pages/5_🔄_Handover.py
import streamlit as st
from components.ui import apply_theme, page_header, card
from components.staff_shared import pick_staff_and_patient
from app.medical_staff_service import MedicalStaffService


st.set_page_config(page_title="Handover", page_icon="🔄", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Shift Handover", "Create & review handover notes.", "🔄")

staff_id, patient = pick_staff_and_patient("handover_pick")
if not patient:
    st.stop()
pid = patient["id"]

with card("New handover"):
    shift = st.selectbox("Shift", ["Morning","Evening","Night"], index=0, key=f"h_shift_{pid}")
    summary = st.text_area("Summary", key=f"h_summary_{pid}")
    if st.button("🗒️ Save handover", type="primary", key=f"h_add_{pid}"):
        h = svc.add_handover(staff_id, pid, shift, summary)
        st.success(f"Handover saved at {h.timestamp}")

with card("Recent handover"):
    hs = svc.list_handover(pid, limit=20)
    if not hs: st.caption("No handover notes yet.")
    else:
        for h in hs:
            st.write(f"• **{h['timestamp']}** — **{h['shift']}** — {h['summary']} (by {h['staff_id']})")
