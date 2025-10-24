import streamlit as st
from components.ui import apply_desktop_css, page_title
from services.data_store import add_mar_entry, list_assigned_patients

st.set_page_config(page_title="Medication • MAR", page_icon="💊", layout="wide")
apply_desktop_css()

nurse_id = st.session_state["nurse_id"]
page_title("Medication Administration Record (MAR)", "Record doses given to assigned patients")

patients = list_assigned_patients(nurse_id)
if not patients:
    st.info("No patients assigned.")
else:
    pid = st.selectbox(
        "Patient",
        [p["id"] for p in patients],
        format_func=lambda pid: next(p["name"] for p in patients if p["id"] == pid),
    )

    with st.form("mar_form"):
        c1, c2, c3 = st.columns(3)
        with c1: drug = st.text_input("Drug", placeholder="Paracetamol")
        with c2: dose = st.text_input("Dose", placeholder="500 mg")
        with c3: route = st.selectbox("Route", ["Oral", "IV", "IM", "Subcutaneous", "Topical"])
        submitted = st.form_submit_button("Record Administration")

    if submitted:
        try:
            entry = add_mar_entry(nurse_id, pid, drug, dose, route)
            st.success(f"Recorded • {entry['drug']} {entry['dose']} via {entry['route']} • {entry['ts']}")
        except Exception as e:
            st.error(str(e))
