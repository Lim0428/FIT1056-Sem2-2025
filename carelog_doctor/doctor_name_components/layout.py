# doctor_name_components/layout.py
from __future__ import annotations
import streamlit as st

# Small CSS fallback so .pill / .muted look good even without theme extras
_FALLBACK_CSS = """
<style>
  .pill{
    display:inline-flex; align-items:center; justify-content:center;
    padding:2px 8px; border-radius:999px; font-size:12px; font-weight:600;
    background:rgba(148,163,184,0.15); color:#E5E7EB; border:1px solid rgba(148,163,184,0.35);
  }
  .muted{ color:#9AA4B2; }
</style>
"""
import streamlit as st

def topbar():
    st.markdown(
        """
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:22px; font-weight:700;">CareLog • Doctor Portal</span>
            <span class="pill">v2.0</span>
          </div>
          <div class="muted" style="font-size:14px;">
            Secure • RBAC • Consent-gated
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

def sidebar_menu() -> str:
    with st.sidebar:
        st.markdown("### Navigation")
        choice = st.radio(
            "Go to",
            [
                "Dashboard",
                "My Profile",
                "Patients",
                "Encounters",
                "Appointments",
                "Appointment History",
                "Messages",
            ],
            label_visibility="collapsed",
            index=0,
            key="nav_menu_radio",          # ← explicit, unique key
        )
    return choice



def sidebar_menu() -> str:
    with st.sidebar:
        st.markdown("### Navigation")
        choice = st.radio(
            "Go to",
            [
                "Dashboard",
                "My Profile",
                "Patients",
                "Encounters",
                "Appointments",
                "Appointment History",   # ← new subpage
                "Messages",
            ],
            label_visibility="collapsed",
            index=0,
        )
        st.markdown("<div class='muted' style='margin-top:6px;'>Use the menu to navigate.</div>", unsafe_allow_html=True)
    return choice
