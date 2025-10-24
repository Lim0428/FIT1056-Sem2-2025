import streamlit as st

st.set_page_config(page_title="CareLog • Nurse Portal", page_icon="🩺", layout="wide")

if "nurse_id" not in st.session_state:
    st.session_state["nurse_id"] = "nurse_1"

st.sidebar.title("Navigation")
st.sidebar.page_link("pages/1_🏥_Dashboard.py", label="Dashboard")
st.sidebar.page_link("pages/2_👤_Patients.py", label="Patients")
st.sidebar.page_link("pages/3_💊_Medication_MAR.py", label="Medication (MAR)")
st.sidebar.page_link("pages/4_📈_Vitals_Notes.py", label="Vitals & Notes")
st.sidebar.page_link("pages/5_🗓️_Tasks.py", label="Tasks")
st.sidebar.page_link("pages/6_🔔_Notifications.py", label="Notifications")
st.sidebar.page_link("pages/7_💬_Messages.py", label="Messages")
st.sidebar.divider()
st.sidebar.caption("Secure • RBAC • Audit-logged")
st.sidebar.success("Logged in as: nurse_1 (demo)")

st.title("CareLog • Nurse Portal")
st.caption("Desktop experience optimized for large screens.")
