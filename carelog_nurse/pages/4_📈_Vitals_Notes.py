import streamlit as st
from components.ui import apply_desktop_css, page_title
from services.data_store import add_vitals, add_note, list_assigned_patients

st.set_page_config(page_title="Vitals & Notes", page_icon="📈", layout="wide")
apply_desktop_css()

nurse_id = st.session_state["nurse_id"]
page_title("Vitals & Notes", "Record observations and care notes")

patients = list_assigned_patients(nurse_id)
if not patients:
    st.info("No patients assigned.")
else:
    pid = st.selectbox("Patient", [p["id"] for p in patients],
                       format_func=lambda pid: next(p["name"] for p in patients if p["id"] == pid))
    st.subheader("Vitals")
    c1, c2, c3, c4 = st.columns(4)
    with c1: temp = st.number_input("Temperature (°C)", 34.0, 43.0, 36.7, step=0.1)
    with c2: hr   = st.number_input("Heart Rate (bpm)", 20, 220, 78)
    with c3: sys  = st.number_input("Systolic (mmHg)", 70, 220, 118)
    with c4: dia  = st.number_input("Diastolic (mmHg)", 40, 140, 76)

    if st.button("Save Vitals"):
        try:
            add_vitals(nurse_id, pid, {"temp_c": temp, "hr_bpm": hr, "bp_sys": sys, "bp_dia": dia})
            st.success("Vitals saved to timeline.")
        except Exception as e:
            st.error(str(e))

    st.subheader("Care Note")
    note = st.text_area("Note", placeholder="Patient resting; mild pain after dressing change.", height=140)

    if st.button("Save Note"):
        try:
            add_note(nurse_id, pid, note.strip())
            st.success("Note saved to timeline.")
        except Exception as e:
            st.error(str(e))
