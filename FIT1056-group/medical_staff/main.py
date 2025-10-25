# medical_staff/main.py
import streamlit as st
from components.ui import apply_theme, card, page_header, require_auth

# ---------- Page config & theme ----------
st.set_page_config(page_title="CareLog • Staff", page_icon="🩺", layout="wide")
apply_theme()

# ---------- Auth (very lightweight stub) ----------
# This is a minimal sign-in to satisfy pages that call `require_auth()`.
# In your real app, replace with a proper auth flow.
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = ""
if "auth_name" not in st.session_state:
    st.session_state["auth_name"] = ""
if "auth_locked" not in st.session_state:
    st.session_state["auth_locked"] = False
if "auth_fail_count" not in st.session_state:
    st.session_state["auth_fail_count"] = 0

def do_logout():
    st.session_state["auth_user"] = ""
    st.session_state["auth_name"] = ""
    st.session_state["auth_locked"] = False
    st.session_state["auth_fail_count"] = 0

with st.sidebar:
    st.title("Medical Staff")
    st.page_link("pages/0_🏠_Dashboard.py",     label="🏠 Dashboard")
    st.page_link("pages/1_🌡️_Vitals.py",       label="🌡️ Vitals")
    st.page_link("pages/2_💊_MAR.py",          label="💊 Medication (MAR)")
    st.page_link("pages/3_📝_Observations.py",  label="📝 Observations")
    st.page_link("pages/4_✅_Tasks.py",         label="✅ Tasks")
    st.page_link("pages/5_🔄_Handover.py",      label="🔄 Handover")
    st.page_link("pages/6_📅_Appointments.py",  label="📅 Appointments")
    st.page_link("pages/7_💬_Messages.py",      label="💬 Messages")
    st.page_link("pages/8_📄_Documents.py",     label="📄 Documents")
    st.page_link("pages/9_🧾_Audit.py",         label="🧾 Audit")

# ---------- Sign-in / header ----------
if not st.session_state["auth_user"]:
    page_header("CareLog • Medical Staff", "Please sign in to continue.", "🩺")
    with card("Sign in"):
        # NOTE: This is intentionally simple. Replace with real auth later.
        col1, col2 = st.columns([2, 1])
        with col1:
            staff_id = st.text_input("Staff ID", placeholder="e.g., S001")
            staff_name = st.text_input("Your name (optional)", placeholder="e.g., Emily")
        with col2:
            if st.session_state["auth_locked"]:
                st.error("Account temporarily locked after 3 failed attempts. Please reload the app.")
            else:
                # Dummy password field to show a flow; not verified here.
                pwd = st.text_input("Password", type="password", placeholder="••••••••")
                if st.button("Sign in", use_container_width=True):
                    # Minimal check: require non-empty staff_id and password
                    if staff_id.strip() and pwd.strip():
                        st.session_state["auth_user"] = staff_id.strip()
                        st.session_state["auth_name"] = (staff_name or staff_id).strip()
                        st.session_state["auth_fail_count"] = 0
                        st.success("Signed in.")
                        st.experimental_rerun()
                    else:
                        st.session_state["auth_fail_count"] += 1
                        if st.session_state["auth_fail_count"] >= 3:
                            st.session_state["auth_locked"] = True
                        st.error("Sign in failed. Please provide Staff ID and Password.")
    st.stop()

# If signed in, show welcome + quick tips
greet = f"Welcome back, {st.session_state['auth_name'] or st.session_state['auth_user']}."
page_header("CareLog • Medical Staff", greet, "🩺")

# Optional sign-out
with st.sidebar:
    st.write("---")
    if st.button("Sign out"):
        do_logout()
        st.experimental_rerun()

with card("Quick tips"):
    st.write(
        "- Use **Dashboard** to confirm the app is running.\n"
        "- Each page starts with a **Patient & Staff picker**.\n"
        "- Data is saved into JSON under the `data/` folder.\n"
        "- If a page asks you to log in, it uses `require_auth()`."
    )
