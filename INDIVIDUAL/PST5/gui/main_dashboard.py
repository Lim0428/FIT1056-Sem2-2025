# gui/main_dashboard.py
import streamlit as st
from app.schedule import ScheduleManager
from app.admin_utils import init_logger, backup_data

# Core pages
from gui.theme import apply_theme
from gui.components import page_header, sidebar_persona
from gui.roster_pages import show_roster_page
from gui.enroll_page import show_enroll_student_page
from gui.course_page import course_page
from gui.lesson_pages import show_lesson_page
from gui.attendance_pages import show_attendance_page
from gui.finance_pages import show_finance_page
from gui.grade_pages import show_grade_page
from gui.feedback_pages import show_feedback_page
from gui.teacher_page import teacher_page as show_teacher_page
from gui.student_pages import show_student_management_page  # not shown to student
from gui.register_student import show_register_student
from gui.lists_hub import show_lists_hub



# Student pages (split)
from gui.student_checkin import show_student_checkin
from gui.student_feedback import show_student_feedback
from gui.student_courses import show_student_courses
from gui.student_grades import show_student_grades

# Auth
from gui.auth import allowed_pages_for, login_ui, logout_button,change_password_ui

LOG_PATH = "msms.log"
DATA_PATH = "data/msms.json"
BACKUP_DIR = "backups"

def _get_manager() -> ScheduleManager:
    if "manager" in st.session_state:
        mgr = st.session_state.manager
        required_attrs = [
            "verify_login",
            "eligible_courses_for_student_now",
            "_lessons_today",
            "_lessons_in_time_window",
        ]
        if any(not hasattr(mgr, a) for a in required_attrs):
            st.session_state.manager = ScheduleManager()
            return st.session_state.manager
        return mgr
    st.session_state.manager = ScheduleManager()
    return st.session_state.manager

def _setup_once():
    if st.session_state.get("setup_done"):
        return
    init_logger(LOG_PATH)
    try:
        backup_data(DATA_PATH, BACKUP_DIR)
    except Exception as e:
        st.toast(f"Startup backup failed: {e}")
    st.session_state["setup_done"] = True

def _pages_map():
    return {
        # Student pages (you already have these wired)
        "Check-in":        show_student_checkin,
        "Submit Feedback": show_student_feedback,
        "My Courses":      show_student_courses,
        "My Grades":       show_student_grades,

        "Directory":       show_lists_hub,

        # Existing shared/staff pages
        "Daily Roster":    show_roster_page,
        "Student Enrollment":show_enroll_student_page,
        "Register Student":show_register_student,
        "Courses":         course_page,
        "Lessons":         show_lesson_page,
        "Attendance":      show_attendance_page,
        "Finance":         show_finance_page,      # transactional finance page
        "Grades":          show_grade_page,
        "Student Feedback":show_feedback_page,
        "Register Teacher":show_teacher_page,
        "Students":        show_student_management_page,  # optional internal page
    }


def launch():
    st.set_page_config(page_title="Music School Management System", layout="wide")

    # NEW: apply CSS theme
    apply_theme()

    _setup_once()
    page_header("Music School Management System", "Manage students, teachers, courses & finance.")

    manager = _get_manager()

    # Login
    user = login_ui(manager)

    if not user:
        st.stop()

    # Sidebar persona + logout + backup
    with st.sidebar:
        if st.button("🔄 Reset Manager (reload data)"):
            st.session_state.pop("manager", None)
            st.rerun()
        sidebar_persona(user, manager)
        logout_button()
        change_password_ui(manager, user)
        if user.get("role") in {"schedule_manager", "admin"}:
            if st.button("🧰 Backup Now"):
                try:
                    backup_data(DATA_PATH, BACKUP_DIR)
                    st.success("Backup completed.")
                except Exception as e:
                    st.error(f"Backup failed: {e}")

    # Navigation as you already have
    pages_map = _pages_map()
    allowed = allowed_pages_for(user) or list(pages_map.keys())
    labels = [lbl for lbl in pages_map if lbl in allowed]
    if st.session_state.get("nav") not in labels:
        st.session_state.pop("nav", None)

    page = st.sidebar.radio("Navigate", options=labels, index=0, key="nav")

    render = pages_map[page]
    render(manager)

if __name__ == "__main__":
    launch()
