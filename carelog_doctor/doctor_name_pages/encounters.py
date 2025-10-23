import streamlit as st
from datetime import datetime
from doctor_name_services.patients import patient_miniview
from doctor_name_services.encounters import (
    list_encounters_for_patient, add_encounter_version, upload_attachment, list_attachments
)
from doctor_name_services.consent import ensure_doctor_can_view_patient

def page_encounters(store):
    st.subheader("Clinical Documentation")
    patients = store.list_assigned_or_consented_patients()
    pid_options = {f"{p['name']} (#{p['id']})": p["id"] for p in patients}
    if not pid_options:
        st.info("No patients available under current permissions.")
        return

    sel = st.selectbox("Select patient", list(pid_options.keys()))
    patient_id = pid_options[sel]
    p = patient_miniview(store, patient_id)

    if not ensure_doctor_can_view_patient(store, patient_id):
        st.error("Access blocked by consent gate. This event is logged.")
        return

    with st.expander("Patient Summary", expanded=True):
        st.write({
            "Conditions": p.get("conditions", []),
            "Allergies": p.get("allergies", []),
            "Medications": p.get("medications", []),
            "History": p.get("history", [])
        })

    st.markdown("#### Encounter Notes & Diagnosis (Versioned)")
    history = list_encounters_for_patient(store, patient_id)
    if history:
        for enc in history:
            with st.container():
                st.markdown(f"**Encounter #{enc['encounter_id']}** • {enc['created_at']}")
                st.write(enc["latest"])
                with st.expander("View previous versions"):
                    for v in enc.get("versions", []):
                        st.write(v)
    else:
        st.caption("No encounters yet.")

    st.markdown("#### Add/Update Encounter")
    with st.form("encounter_form"):
        diagnosis = st.text_input("Diagnosis")
        notes = st.text_area("Notes / Assessment")
        orders = st.text_area("Orders / Recommendations (labs, imaging, medication instructions)")
        submitted = st.form_submit_button("Save encounter")
        if submitted:
            payload = {
                "diagnosis": diagnosis,
                "notes": notes,
                "orders": orders,
                "timestamp": datetime.now().isoformat()
            }
            add_encounter_version(store, patient_id, payload)
            st.success("Saved. Version history updated.")
            st.rerun()

    st.markdown("#### Attachments")
    up = st.file_uploader("Upload attachment (PDF/Image)", type=["pdf","png","jpg","jpeg"])
    if up is not None:
        path = upload_attachment(store, patient_id, up)
        st.success(f"Uploaded to {path}")
    att = list_attachments(store, patient_id)
    if att:
        st.write(att)
