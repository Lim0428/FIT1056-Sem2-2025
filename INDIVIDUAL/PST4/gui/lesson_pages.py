import streamlit as st

def show_lesson_page(manager):
    st.header("Lesson Management")

    st.subheader("All Scheduled Lessons")
    lesson_table = []
    for c in manager.courses:
        teacher = manager.find_teacher_by_id(c.teacher_id)
        for L in c.lessons:
            lesson_table.append({
                "Lesson ID": L.get("lesson_id"),
                "Course": c.name,
                "Teacher": teacher.name if teacher else "Unknown",
                "Day": L.get("day", "TBD"),
                "Start Time": L.get("start_time", "TBD"),
                "Room": L.get("room", "TBD"),
                "Cancelled": "Yes" if L.get("cancelled") else "No"
            })
    if lesson_table:
        st.dataframe(lesson_table)
    else:
        st.info("No lessons scheduled yet.")


    st.subheader("Add Lesson")
    with st.form("add_lesson_form"):
        cid = st.selectbox("Course", [c.id for c in manager.courses], key="add_course")
        day = st.text_input("Day (e.g. Monday)")
        start_time = st.text_input("Start Time (HH:MM)")
        room = st.text_input("Room")
        submitted = st.form_submit_button("Add Lesson")
        if submitted:
            new_lesson = manager.add_lesson(cid, day, start_time, room)
            st.success(f"Added Lesson {new_lesson['lesson_id']} to Course {cid}")

    st.divider()

    st.subheader("Cancel Lesson")
    with st.form("cancel_form"):
        cid = st.selectbox("Course", [c.id for c in manager.courses])
        course = manager.find_course_by_id(cid)
        lid = st.selectbox("Lesson", [L["lesson_id"] for L in course.lessons])
        reason = st.text_input("Reason")
        submitted = st.form_submit_button("Cancel Lesson")
        if submitted:
            manager.cancel_lesson(cid, lid, reason)
            st.success(f"Lesson {lid} cancelled")

    st.subheader("Reschedule Lesson")
    with st.form("reschedule_form"):
        cid = st.selectbox("Course (Reschedule)", [c.id for c in manager.courses])
        course = manager.find_course_by_id(cid)
        lid = st.selectbox("Lesson ID", [L["lesson_id"] for L in course.lessons])
        new_day = st.text_input("New Day")
        new_time = st.text_input("New Time")
        new_room = st.text_input("New Room")
        submitted = st.form_submit_button("Reschedule")
        if submitted:
            manager.reschedule_lesson(cid, lid, new_day, new_time, new_room)
            st.success("Lesson rescheduled")
