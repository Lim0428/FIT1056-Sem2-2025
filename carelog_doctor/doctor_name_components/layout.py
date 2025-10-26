# doctor_name_components/layout.py
from __future__ import annotations
import streamlit as st

def topbar() -> None:
    # Minimal topbar – your existing one is fine; theme will handle colors
    st.markdown(
        """
        <div style="height:8px"></div>
        """,
        unsafe_allow_html=True,
    )

def sidebar_menu() -> str | None:
    with st.sidebar:
        st.markdown("### Navigation")
        choice = st.radio(
            "Go to",
            options=[
                "Dashboard",
                "My Profile",
                "Patients",
                "Encounters",
                "Appointments",
                "Appointment History",
                "Messages",
            ],
            index=None,
            label_visibility="collapsed",
            key="sidebar_nav_radio",
        )
        return choice
