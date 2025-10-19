import streamlit as st

def show_grade_page(manager):
    st.header("Grades")

    student_dict = {s.name: s.id for s in manager.students}
    course_dict = {c.name: c.id for c in manager.courses}
    teacher_dict = {t.name: t.id for t in manager.teachers}

    st.subheader("Assign Grade")
    with st.form("grade_form"):
        teacher_name = st.selectbox("Teacher", list(teacher_dict.keys()))
        student_name = st.selectbox("Student", list(student_dict.keys()))
        course_name = st.selectbox("Course", list(course_dict.keys()))
        grade = st.selectbox("Grade", ["A", "B", "C", "D", "F"])
        note = st.text_area("Note (optional)")
        submitted = st.form_submit_button("Assign")
        if submitted:
            tid = teacher_dict[teacher_name]
            sid = student_dict[student_name]
            cid = course_dict[course_name]
            success = manager.assign_grade(tid, sid, cid, grade, note)
            if success:
                st.success(f"Grade {grade} assigned to {student_name} in {course_name} by {teacher_name}")
            else:
                st.error("Failed to assign grade. Check teacher/course permissions.")

    st.subheader("All Student Grades")
    if not manager.grades:
        st.info("No grades assigned yet.")
    else:
        grade_table = []
        for g in manager.grades:
            student = manager.find_student_by_id(g["student_id"])
            course = manager.find_course_by_id(g["course_id"])
            teacher = manager.find_teacher_by_id(g["teacher_id"])
            grade_table.append({
                "Student": student.name if student else g["student_id"],
                "Course": course.name if course else g["course_id"],
                "Teacher": teacher.name if teacher else g["teacher_id"],
                "Grade": g["grade"],
                "Note": g.get("note", ""),
                "Timestamp": g["timestamp"]
            })
        st.dataframe(grade_table)