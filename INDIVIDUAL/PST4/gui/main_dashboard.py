import streamlit as st
from app.schedule import ScheduleManager
from gui.attendance_pages import show_attendance_page
from gui.student_pages import show_student_management_page
from gui.course_page import course_page
from gui.payment_pages import show_payment_page
from gui.grade_pages import show_grade_page
from gui.feedback_pages import show_feedback_page
from gui.lesson_pages import show_lesson_page
from gui.teacher_page import teacher_page
from gui.roster_pages import show_roster_page
from gui.enroll_page import show_enroll_student_page

def launch():
    st.set_page_config(layout="wide", page_title="Music School Management System")

    # Instantiate the "brain" of our app ONCE and store it in the session state.
    if 'manager' not in st.session_state:
        st.session_state.manager = ScheduleManager()

# Load the manager
    manager = ScheduleManager()

    # Sidebar navigation
    st.sidebar.title("MSMS Dashboard")
    page = st.sidebar.radio(
        "Go to",
        ["Students","Daily Roster","Enroll Student","Courses", "Teachers", "Finance", "Attendance", "Grades", "Feedback", "Lessons"]
    )

    # Router
    if page == "Students":
        show_student_management_page(manager)
    elif page == "Daily Roster":
        show_roster_page(manager)
    elif page == "Enroll Student":
        show_enroll_student_page(manager)
    elif page == "Courses":
        course_page(manager)
    elif page == "Teachers":
        teacher_page(manager)
    elif page == "Finance":
        show_payment_page(manager)
    elif page == "Attendance":
        show_attendance_page(manager)
    elif page == "Grades":
        show_grade_page(manager)
    elif page == "Feedback":
        show_feedback_page(manager)
    elif page == "Lessons":
        show_lesson_page(manager)