# medical_staff/pages/8_📄_Documents.py
import streamlit as st
from components.ui import apply_theme, page_header, card
from components.staff_shared import pick_staff_and_patient
from app.medical_staff_service import MedicalStaffService


st.set_page_config(page_title="Documents", page_icon="📄", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Documents", "Upload & list patient documents.", "📄")

staff_id, patient = pick_staff_and_patient("doc_pick")
if not patient:
    st.stop()
pid = patient["id"]

with card("Upload document"):
    up = st.file_uploader("Upload a PDF/Image", type=["pdf","png","jpg","jpeg"], key=f"doc_up_{pid}")
    kind = st.selectbox("Type", ["Report","Referral","Imaging","Other"], index=0, key=f"doc_kind_{pid}")
    note = st.text_input("Note (optional)", "", key=f"doc_note_{pid}")
    if up and st.button("⬆️ Upload", type="primary", key=f"doc_upload_{pid}"):
        data = up.getvalue()
        doc = svc.add_document(staff_id, pid, up.name, kind, note, data)
        st.success(f"Uploaded {doc.name} at {doc.uploaded_at}")

with card("Patient documents"):
    docs = svc.list_documents(pid, limit=50)
    if not docs: st.caption("No documents.")
    else:
        for d in docs:
            st.write(f"• **{d['uploaded_at']}** — {d['name']} ({d['kind']}) — {d['note']}")
            st.caption(d["path"])
