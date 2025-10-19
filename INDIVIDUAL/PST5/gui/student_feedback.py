# gui/student_feedback.py
import streamlit as st

def show_student_feedback(manager):
    st.header("Submit Feedback")

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
    courses = [c for c in courses if c]
    if not courses:
        st.info("You are not enrolled in any courses.")
        return

    label_to_id = {f"{c.id} — {c.name} ({c.instrument})": c.id for c in courses}
    label = st.selectbox("Course", list(label_to_id.keys()))
    comment = st.text_area("Your feedback")
    if st.button("Submit"):
        if comment.strip():
            manager.submit_feedback(sid, label_to_id[label], comment.strip())
            st.success("Feedback submitted.")
        else:
            st.warning("Please enter some feedback.")
