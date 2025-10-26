import streamlit as st
from counselor_name_components.ui import apply_theme, top_nav, require_auth

st.set_page_config(page_title="CareLog – Counselor", page_icon="🧠", layout="wide")
apply_theme()

# Sign-in first
require_auth()

# Sidebar navigation (requires 'pages/' folder next to this file)
top_nav("Dashboard")

# Home content
st.title("CareLog – Counselor Portal")
st.write("Use the sidebar navigation to access your tools.")

# Quick links
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/2_🧾_Session_Notes.py", label="Open Session Notes →")
with col2:
    st.page_link("pages/4_📅_Appointments.py", label="Manage Appointments →")
with col3:
    st.page_link("pages/5_💬_Messages.py", label="Open Messages →")
