# nurse/nurse_app.py
import streamlit as st
from components.ui import apply_theme

st.set_page_config(page_title="CareLog — Nurse", page_icon="🩺", layout="wide")
apply_theme()

st.sidebar.title("Nurse Portal")
st.sidebar.caption("All core functions (demo)")
st.sidebar.success("Logged in as: Sarah Lim (demo)")

st.sidebar.markdown("---")
st.sidebar.write("Data file → `data/carelog_nurse.json` (auto-created).")
st.sidebar.info("Use the sidebar page list to navigate features.")
