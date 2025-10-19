# gui/student_checkin.py
import streamlit as st

def show_student_checkin(manager):
    st.header("Check-in")

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

    # Show *only* courses eligible right now
    eligible_ids = set(
        manager.eligible_courses_for_student_now(sid, window_minutes=90)
        if hasattr(manager, "eligible_courses_for_student_now") else []
    )
    eligible_courses = [c for c in courses if c.id in eligible_ids]

    if not eligible_courses:
        st.warning(
            "No classes are currently available to check in.\n\n"
            "• Either there is no lesson **today**, or\n"
            "• The lesson **hasn't started yet / already passed** the time window (±90 min), or\n"
            "• The lesson was **cancelled**."
        )
        return

    label_to_id = {f"{c.id} — {c.name} ({c.instrument})": c.id for c in eligible_courses}
    label = st.selectbox("Select a course (eligible now)", list(label_to_id.keys()))

    if st.button("Check-in"):
        ok = manager.check_in(sid, label_to_id[label], window_minutes=90)
        if ok:
            st.success("Checked in successfully.")
        else:
            st.error("Check-in failed. Please try again or contact the front desk.")
