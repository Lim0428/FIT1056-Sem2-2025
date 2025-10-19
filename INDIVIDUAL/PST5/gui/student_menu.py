# gui/student_menu.py
import streamlit as st

def _student_courses(manager, student_id):
    stu = manager.find_student_by_id(int(student_id))
    if not stu:
        return []
    courses = []
    for cid in getattr(stu, "enrolled_course_ids", []):
        c = manager.find_course_by_id(cid)
        if c:
            courses.append(c)
    return courses

def show_student_menu(manager):
    st.header("Student Menu")

    user = st.session_state.get("user")
    if not user or user.get("role") != "student":
        st.info("This page is for students.")
        return
    sid = int(user["user_id"])

    st.subheader("1) Check-in")
    courses = _student_courses(manager, sid)
    if courses:
        course_label_map = {f"{c.id} — {c.name} ({c.instrument})": c.id for c in courses}
        sel = st.selectbox("Select your course to check in", list(course_label_map.keys()), key="student_checkin_sel")
        if st.button("Check-in"):
            ok = manager.check_in(sid, course_label_map[sel])
            if ok:
                st.success("Checked in successfully.")
            else:
                st.error("Check-in failed. Make sure you are enrolled in that course.")
    else:
        st.info("You are not enrolled in any courses yet.")

    st.divider()
    st.subheader("2) Submit Feedback")
    if courses:
        fb_sel = st.selectbox("Course", list(course_label_map.keys()), key="student_fb_sel")
        comment = st.text_area("Your feedback", key="student_fb_txt")
        if st.button("Submit Feedback"):
            if comment.strip():
                manager.submit_feedback(sid, course_label_map[fb_sel], comment.strip())
                st.success("Feedback submitted.")
            else:
                st.warning("Please enter some feedback before submitting.")
    else:
        st.info("No courses to submit feedback for.")

    st.divider()
    st.subheader("3) View Enrolled Courses")
    if courses:
        st.table([{"Course ID": c.id, "Course": c.name, "Instrument": c.instrument} for c in courses])
    else:
        st.info("No enrolled courses to show.")

    st.divider()
    st.subheader("4) View Grades")
    grades = [g for g in manager.grades if int(g.get("student_id", -1)) == sid]
    if grades:
        # Display newest first
        grades = sorted(grades, key=lambda g: g.get("timestamp", ""), reverse=True)
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
