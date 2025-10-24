# doctor_name_pages/dashboard.py
import streamlit as st

# Widgets from doctor_name_components/widgets.py
from doctor_name_components.widgets import (
    kpi_stat,
    revenue_chart,
    today_appointments_list,
    profile_card,
    messages_panel,                 # interactive messages
    duty_hour_strip_interactive,    # 7-day chips
    plot_day_work_line,             # per-day line chart
    overall_appointment_card,
    appointment_history_list,       # expects (store, ...)
)

def page_dashboard(store):
    """Main Doctor dashboard page."""
    st.markdown("### Dashboard")

    # ---------------- KPI Row ----------------
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1], gap="large")
    with c1:
        kpi_stat("Assigned Patients", store.count_assigned_patients())
    with c2:
        kpi_stat("Appointments Today", store.count_today_appts())
    with c3:
        kpi_stat("Unread Messages", store.count_unread_messages())
    with c4:
        kpi_stat("Recent Edits (7d)", store.count_recent_edits())

    st.write("")

    # -------- Align first row cards (same container + min-height) --------
    st.markdown(
        """
        <style>
          /* Make the 1st row cards (revenue / today / profile) the same min height */
          .dash-row-1 .stContainer { min-height: 360px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="dash-row-1">', unsafe_allow_html=True)
    left, mid, right = st.columns([7, 5, 5], gap="large")

    # Revenue
    with left:
        with st.container(border=True):
            st.markdown(
                "**Revenue**  \n"
                "<span class='muted'>Your average per week is 57%.</span>",
                unsafe_allow_html=True,
            )
            years  = ["2023", "2022", "2021", "2020", "2019", "2018", "2017"]
            values = [22000, 24000, 18000, 12000, 15000, 8000, 6000]
            revenue_chart(
                years,
                values,
                x_label="Revenue (RM)",
                y_label="Year",
                bg_color="#0A1930",
                bar_color="#4FC3F7",
                grid=True,
            )

    # Today's Appointment
    with mid:
        with st.container(border=True):
            st.markdown("**Today's Appointment**")
            today_appointments_list(store)  # uses JSON data; rows are clickable

    # Your Profile (now aligned with the other two)
    with right:
        with st.container(border=True):
            st.markdown("**Your Profile**")
            profile_card(store)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # ---------------- Second Row ----------------
    l2, m2, r2 = st.columns([7, 5, 5], gap="large")

    # Duty hour (strip + line)
    with l2:
        with st.container(border=True):
            st.markdown(
                "**Duty Hour**  \n"
                "<span class='muted'>Avg Duty Hour 57 h</span>",
                unsafe_allow_html=True,
            )
            selected_date = duty_hour_strip_interactive(state_key="duty_selected")
            plot_day_work_line(selected_date)
        overall_appointment_card()

    # Appointment History (only 2 items + gradient 'See more')
    with m2:
        with st.container(border=True):
            st.markdown(
                "**Appointment History**  \n"
                "<span class='muted'>Recap this month.</span>",
                unsafe_allow_html=True,
            )

            # Only show the 2 latest past appointments on the dashboard
            appointment_history_list(store, month_only=True, limit=2, key_prefix="dash_hist")

            # Transparent button with gradient border
            st.markdown(
                """
                <style>
                #see-more-wrap button {
                    background: transparent !important;
                    color: #E6F4FF !important;
                    border-width: 1.5px !important;
                    border-style: solid !important;
                    border-radius: 14px !important;
                    border-image: linear-gradient(90deg, #4FC3F7 0%, #2E5AAC 100%) 1 !important;
                    box-shadow: none !important;
                    transition: box-shadow .15s ease, transform .05s ease;
                    padding-top: 10px !important;
                    padding-bottom: 10px !important;
                }
                #see-more-wrap button:hover {
                    box-shadow:
                      0 0 0 3px rgba(79,195,247,0.12) inset,
                      0 6px 24px rgba(46,90,172,0.25) !important;
                }
                #see-more-wrap button:active { transform: translateY(1px); }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div id="see-more-wrap">', unsafe_allow_html=True)
            if st.button("See more", type="secondary", key="dash_hist_see_more_grad"):
                st.session_state["nav"] = "Appointment History"
                st.session_state["_route_push"] = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # Messages panel
    with r2:
        with st.container(border=True):
            st.markdown("**Message**")
            messages_panel(store)
