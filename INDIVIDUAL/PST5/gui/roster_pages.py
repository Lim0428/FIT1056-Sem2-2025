# gui/roster_pages.py
import streamlit as st
import pandas as pd
from gui.components import stat_cards

def show_roster_page(manager):
    """Renders the daily roster and check-in functionality."""
    st.header("Daily Roster")

    # Pick a day
    day = st.selectbox(
        "Select a day",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    )

    # Use the public API you already have
    roster = manager.get_day_roster(day)

    # KPIs — count using the roster we just fetched (avoid _lessons_today(...))
    today_total = len(roster) if roster else 0
    stat_cards([
        {"label": "Lessons Today", "value": today_total, "help": f"Scheduled on {day}", "icon": "📅"},
        {"label": "Teachers", "value": len(manager.teachers), "help": "Active", "icon": "👩‍🏫"},
        {"label": "Courses", "value": len(manager.courses), "help": "Available", "icon": "🎼"},
    ])
    st.write("")

    # Render roster
    if roster:
        # Accept list[dict] or DataFrame
        if isinstance(roster, pd.DataFrame):
            st.dataframe(roster, use_container_width=True)
        else:
            st.dataframe(roster, use_container_width=True)
    else:
        st.info(f"No classes scheduled on {day}.")

    # ---------------- Optional: student check-in block (unchanged) ----------------
    st.subheader("Student Check-in")
    with st.form("check_in_form"):
        student_list = {s.name: s.id for s in manager.students}
        course_list = {c.name: c.id for c in manager.courses}

        if not student_list or not course_list:
            st.caption("Add students and courses to enable check-in.")
            submitted = False
        else:
            selected_student_name = st.selectbox("Select Student", list(student_list.keys()))
            selected_course_name = st.selectbox("Select Course", list(course_list.keys()))
            submitted = st.form_submit_button("Check-in Student")

        if submitted:
            student_id = student_list[selected_student_name]
            course_id = course_list[selected_course_name]
            success = manager.check_in(student_id, course_id)
            if success:
                st.success(f"Checked in {selected_student_name} for {selected_course_name}!")
            else:
                st.error("Check-in failed. Is the student enrolled in that course?")
