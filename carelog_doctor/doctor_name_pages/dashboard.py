# doctor_name_pages/dashboard.py
import streamlit as st

# Widgets/components used on the dashboard
from doctor_name_components.widgets import (
    kpi_stat,
    revenue_chart,
    today_appointments_list,
    profile_card,
    messages_panel,                 # interactive messages panel
    duty_hour_strip_interactive,    # 7-day chips
    plot_day_work_line,             # line chart per selected day
    overall_appointment_card,
    appointment_history_list,
)

def page_dashboard(store):
    """Main Doctor dashboard page."""
    st.markdown("### Dashboard")

    # ---- KPI Row -----------------------------------------------------------
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1], gap="large")
    with c1: kpi_stat("Assigned Patients", store.count_assigned_patients())
    with c2: kpi_stat("Appointments Today", store.count_today_appts())
    with c3: kpi_stat("Unread Messages", store.count_unread_messages())
    with c4: kpi_stat("Recent Edits (7d)", store.count_recent_edits())

    st.write("")

    # ---- Main Grid (Revenue • Today's Appointments • Profile) --------------
    left, mid, right = st.columns([7, 5, 5], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("**Revenue**  \n<span class='muted'>Your average per week is 57%.</span>", unsafe_allow_html=True)
            years  = ["2023","2022","2021","2020","2019","2018","2017"]
            values = [22000, 24000, 18000, 12000, 15000, 8000, 6000]
            # Dark blue background, light blue bars, white text (your latest styling)
            revenue_chart(
                years, values,
                x_label="Revenue (RM)", y_label="Year",
                bg_color="#0A1930", bar_color="#4FC3F7", grid=True
            )

    with mid:
        with st.container(border=True):
            st.markdown("**Today's Appointment**")
            today_appointments_list(store)

    with right:
        profile_card(store)

    st.write("")

    # ---- Second Row (Duty Hour • Appointment History • Messages) ----------
    l2, m2, r2 = st.columns([7, 5, 5], gap="large")

    with l2:
        with st.container(border=True):
            st.markdown("**Duty Hour**  \n<span class='muted'>Avg Duty Hour 57 h</span>", unsafe_allow_html=True)
            selected_date = duty_hour_strip_interactive(state_key="duty_selected")
            plot_day_work_line(selected_date)
        overall_appointment_card()

    with m2:
        with st.container(border=True):
            st.markdown("**Appointment History**  \n<span class='muted'>Recap this month.</span>", unsafe_allow_html=True)
            appointment_history_list()

    with r2:
        with st.container(border=True):
            st.markdown("**Message**")
            messages_panel(store)  # clickable list + chat view
