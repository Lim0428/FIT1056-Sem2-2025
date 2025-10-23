import streamlit as st
from datetime import datetime, date
import json, os, uuid, hashlib

st.set_page_config(page_title="Patient Portal", page_icon="🧍", layout="wide")

if "login_user" not in st.session_state or st.session_state.get("login_role") != "Patient":
    st.warning("Please log in as a patient first.")
    st.stop()

user = st.session_state["login_user"]
st.sidebar.success(f"Logged in as {user['name']}")
st.title("🩺 CareLog — Patient Portal")
