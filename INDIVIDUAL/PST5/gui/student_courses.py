# gui/student_courses.py
import streamlit as st

def show_student_courses(manager):
    st.header("My Courses")

    user = st.session_state.get("user")
    if not user or user.get("role") != "student":
        st.info("This page is for students.")
        return
    sid = int(user["user_id"])

    stu = manager.find_student_by_id(sid)
    if not stu:
        st.error("Student not found.")
        return

    enrolled_ids = getattr(stu, "enrolled_course_ids", []) or []
    courses = [manager.find_course_by_id(cid) for cid in enrolled_ids]
    rows = []
    for c in courses:
        if not c:
            continue
        rows.append({"Course ID": c.id, "Course": c.name, "Instrument": c.instrument})
    if rows:
        st.table(rows)
    else:
        st.info("You are not enrolled in any courses.")
