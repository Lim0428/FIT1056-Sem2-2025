import streamlit as st
from components.ui import require_auth, apply_theme, page_header, card
from services.patient import PatientService

st.set_page_config(page_title="Profile & Preferences", page_icon="👤", layout="centered")
apply_theme()
require_auth()

pid = st.session_state.auth_user
svc = PatientService()

page_header("Profile & Preferences", "Personal info, medical notes, and care preferences", "👤")
p = svc.get(pid)

with card("Edit Profile"):
    with st.form("profile_form"):
        name = st.text_input("Full name", value=p.get("name",""))
        gender = st.selectbox("Gender", ["", "Male", "Female", "Other"], index=["","Male","Female","Other"].index(p.get("gender","")))
        medical_details = st.text_area("Medical details (conditions, allergies)", value=p.get("medical_details",""))
        emergency_contact = st.text_input("Emergency contact (name & phone)", value=p.get("emergency_contact",""))

        st.markdown("### Preferences")
        pref_food = st.text_input("Food preference (e.g., halal, low oil, no pork)", value=p.get("pref_food",""))
        pref_language = st.text_input("Preferred language", value=p.get("pref_language",""))
        pref_nurse_gender = st.selectbox("Preferred nurse gender", ["", "Male", "Female", "No preference"],
                                        index=["","Male","Female","No preference"].index(p.get("pref_nurse_gender","")))
        visible_to_non_primary = st.checkbox("Allow non-primary staff to view my medical details",
                                            value=p.get("visible_to_non_primary", False))
        submitted = st.form_submit_button("Save changes")

if submitted:
    svc.update_profile(pid, {
        "name": name,
        "gender": gender,
        "medical_details": medical_details,
        "emergency_contact": emergency_contact,
        "pref_food": pref_food,
        "pref_language": pref_language,
        "pref_nurse_gender": pref_nurse_gender,
        "visible_to_non_primary": visible_to_non_primary
    })
    st.success("Profile updated.")
