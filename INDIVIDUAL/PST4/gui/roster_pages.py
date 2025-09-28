# gui/roster_pages.py
import streamlit as st
import pandas as pd

def show_roster_page(manager):
    """Renders the daily roster and check-in functionality."""
    st.header("Daily Roster")

    # view roster section
    day = st.selectbox("Select a day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    roster = manager.get_day_roster(day)
    if roster:
        st.table(roster)
    else:
        st.info(f"No classes scheduled on {day}.")
    
    # student check in section
    st.subheader("Student Check-in")
    with st.form("check_in_form"):
        # Get lists of student names and course names from the manager.
        student_list = {s.name: s.id for s in manager.students}
        course_list = {c.name: c.id for c in manager.courses}
        
        selected_student_name = st.selectbox("Select Student", student_list.keys())
        selected_course_name = st.selectbox("Select Course", course_list.keys())
        
        submitted = st.form_submit_button("Check-in Student")

        if submitted:
            #convert the selected names back to IDs
            student_id = student_list[selected_student_name]
            course_id = course_list[selected_course_name]

            success = manager.check_in(student_id, course_id)

            if success:
                st.success(f"Checked in {selected_student_name} for {selected_course_name}!")
            else:
                st.error("Check-in failed. See console for details. (Is the student enrolled in that course?)")