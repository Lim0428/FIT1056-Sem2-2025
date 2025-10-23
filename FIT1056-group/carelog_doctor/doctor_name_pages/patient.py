import streamlit as st
from doctor_name_services.patients import search_patients_by_keyword
from doctor_name_components.tables import table_patients

def page_patients(store):
    st.subheader("Patients (Consent/Assignment Required)")
    q = st.text_input("Search by name / ID / contact")
    if q:
        rows = search_patients_by_keyword(store, q)
    else:
        rows = store.list_assigned_or_consented_patients()
    table_patients(rows)
