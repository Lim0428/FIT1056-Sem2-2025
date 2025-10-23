# doctor_name_pages/dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from doctor_name_components.widgets import (
    kpi_stat, revenue_chart, today_appointments_list,
    profile_card, messages_list, duty_hour_strip,
    appointment_history_list, overall_appointment_card,screen_time_card
)
from doctor_name_components.tables import table_appointments

def page_dashboard(store):
    st.markdown("### Dashboard")

    # ===== TOP KPIs (thin row, like the screenshot numbers) =====
    c1, c2, c3, c4 = st.columns([1,1,1,1], gap="large")
    with c1: kpi_stat("Assigned Patients", store.count_assigned_patients())
    with c2: kpi_stat("Appointments Today", store.count_today_appts())
    with c3: kpi_stat("Unread Messages", store.count_unread_messages())
    with c4: kpi_stat("Recent Edits (7d)", store.count_recent_edits())

    st.write("")  # small spacing

    # ===== MAIN GRID (Revenue • Today’s Appointments • Profile) =====
    left, mid, right = st.columns([7,5,5], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("**Revenue**  \n<span class='muted'>Your average per week is 57%.</span>", unsafe_allow_html=True)

            # Example dataset (replace with your own)
            years  = ["2023","2022","2021","2020","2019","2018","2017"]
            values = [22000, 24000, 18000, 12000, 15000, 8000, 6000]

            revenue_chart(
                years, values,
                x_label="Revenue (RM)",
                y_label="Year",
                bg_color="#0A1930",   # dark navy blue
                bar_color="#4FC3F7",  # soft light blue bars
                grid=True
            )



    with mid:
        with st.container(border=True):
            st.markdown("**Today's Appointment**")
            today_appointments_list(store)

    with right:
        profile_card(store)  # compact right-side profile panel

    st.write("")

    # ===== SECOND ROW (Duty Hour • Appointment History • Messages) =====
    l2, m2, r2 = st.columns([7,5,5], gap="large")

    with l2:
        with st.container(border=True):
            screen_time_card(card_title="Duty Hour")   # ← new iOS-like card

        overall_appointment_card()


        overall_appointment_card()  # mini dark card like screenshot bottom-left

    with m2:
        with st.container(border=True):
            st.markdown("**Appointment History**  \n<span class='muted'>Recap this month.</span>", unsafe_allow_html=True)
            appointment_history_list()

    with r2:
        with st.container(border=True):
            st.markdown("**Message**")
            messages_list(store)  # right-side chat list
