import streamlit as st

def show_attendance_page(manager):
    st.header("Attendance")

    # Build lookup dicts
    student_dict = {s.name: s.id for s in manager.students}
    course_dict = {c.name: c.id for c in manager.courses}

    # Check-in form
    st.subheader("Check-in Student")
    with st.form("checkin_form"):
        student_name = st.selectbox("Student", list(student_dict.keys()))
        course_name = st.selectbox("Course", list(course_dict.keys()))
        submitted = st.form_submit_button("Check-in")
        if submitted:
            sid = student_dict[student_name]
            cid = course_dict[course_name]
            manager.check_in(sid, cid)
            st.success(f"Checked in {student_name} for {course_name}")

        
    st.subheader("Attendance Report")
    if not manager.attendance_log:
        st.warning("No attendance records yet.")
    else:
        report = []
        for a in manager.attendance_log:
            s = manager.find_student_by_id(a["student_id"])
            c = manager.find_course_by_id(a["course_id"])
            if not (s and c):
                continue
            report.append({
                "Student": s.name,
                "Course": c.name,
                "Timestamp": a["timestamp"]
            })
        st.dataframe(report)