import streamlit as st
from doctor_name_services.auth import current_doctor
from doctor_name_services.data_store import DataStore

def page_profile(store: DataStore):
    st.subheader("My Profile")
    doc = current_doctor()

    with st.form("profile_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", value=doc.get("name",""))
            specialty = st.text_input("Specialty", value=doc.get("specialty",""))
            qualifications = st.text_input("Qualifications", value=doc.get("qualifications",""))
            license_no = st.text_input("License No.", value=doc.get("license_no",""))
        with col2:
            working_hours = st.text_input("Working Hours", value=doc.get("working_hours",""))
            contact = st.text_input("Contact", value=doc.get("contact",""))
            email_show = st.text_input("Email (read-only)", value=doc.get("email",""), disabled=True)
        submitted = st.form_submit_button("Save Changes", use_container_width=True)
        if submitted:
            store.update_doctor_profile(
                name=name,
                specialty=specialty,
                qualifications=qualifications,
                license_no=license_no,
                working_hours=working_hours,
                contact=contact
            )
            st.success("Profile updated.")
