# gui/student_grades.py
import streamlit as st

def show_student_grades(manager):
    st.header("My Grades")

    user = st.session_state.get("user")
    if not user or user.get("role") != "student":
        st.info("This page is for students.")
        return
    sid = int(user["user_id"])

    grades = [g for g in manager.grades if int(g.get("student_id", -1)) == sid]
    grades = sorted(grades, key=lambda g: g.get("timestamp", ""), reverse=True)
    if grades:
        st.table([
            {
                "Course ID": g.get("course_id"),
                "Grade": g.get("grade"),
                "Note": g.get("note", ""),
                "Timestamp": g.get("timestamp", "")
            } for g in grades
        ])
    else:
        st.info("No grades recorded yet.")
