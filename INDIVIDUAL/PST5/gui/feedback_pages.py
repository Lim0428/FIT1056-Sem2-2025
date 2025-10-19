import streamlit as st

def show_feedback_page(manager):
    st.header("Student Feedback")

    student_dict = {s.name: s.id for s in manager.students}
    course_dict = {c.name: c.id for c in manager.courses}

    st.subheader("Submit Feedback")
    with st.form("feedback_form"):
        student_name = st.selectbox("Student", list(student_dict.keys()))
        course_name = st.selectbox("Course", list(course_dict.keys()))
        comment = st.text_area("Comment")
        submitted = st.form_submit_button("Submit Feedback")
        if submitted:
            sid = student_dict[student_name]
            cid = course_dict[course_name]
            manager.submit_feedback(sid, cid, comment)
            st.success(f"Feedback submitted for {student_name} in {course_name}")


    st.subheader("View Feedback")
    if not manager.feedbacks:
        st.info("No feedback submitted yet.")
    else:
        feedback_data = []
        for fb in manager.feedbacks:
            student = manager.find_student_by_id(fb["student_id"])
            course = manager.find_course_by_id(fb["course_id"])
            feedback_data.append({
                "Student": student.name if student else fb["student_id"],
                "Course": course.name if course else fb["course_id"],
                "Comment": fb["comment"],
                "Timestamp": fb["timestamp"]
            })

        st.dataframe(feedback_data)
