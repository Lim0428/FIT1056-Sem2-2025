import streamlit as st

def show_enroll_student_page(manager):
    st.header("Manage Student Enrollments")

    # ----------------- ENROLL STUDENT -----------------
    st.subheader("Enroll Student in a Course")
    students = manager.get_all_students()
    student_options = {f"{s['ID']}: {s['Name']}": s['ID'] for s in students}

    if students:
        selected_student_enroll = st.selectbox(
            "Select Student to Enroll", 
            student_options.keys(),
            key="enroll_student_select"
        )
        student_id_enroll = student_options[selected_student_enroll]

        # Only show courses the student is NOT already enrolled in
        available_courses = [c for c in manager.courses if student_id_enroll not in c.enrolled_student_ids]
        if available_courses:
            course_options = {f"{c.id}: {c.name}": c.id for c in available_courses}
            selected_course_enroll = st.selectbox(
                "Select Course", 
                course_options.keys(),
                key="enroll_course_select"
            )
            course_id_enroll = course_options[selected_course_enroll]

            if st.button("Enroll Student", key="enroll_button"):
                manager.enroll_student(student_id_enroll, course_id_enroll)
                st.success(f"{selected_student_enroll.split(': ')[1]} enrolled in {selected_course_enroll.split(': ')[1]}.")
        else:
            st.info(f"{selected_student_enroll.split(': ')[1]} is already enrolled in all courses.")
    else:
        st.info("No students available for enrollment.")

    st.markdown("---")  # Separator between sections

    # ----------------- UNENROLL STUDENT -----------------
    st.subheader("Unenroll Student from a Course")

    if students:
        selected_student_unenroll = st.selectbox(
            "Select Student to Unenroll", 
            student_options.keys(),
            key="unenroll_student_select"
        )
        student_id_unenroll = student_options[selected_student_unenroll]

        # Only show courses the student is enrolled in
        enrolled_courses = [c for c in manager.courses if student_id_unenroll in c.enrolled_student_ids]
        if enrolled_courses:
            course_options = {f"{c.id}: {c.name}": c.id for c in enrolled_courses}
            selected_course_unenroll = st.selectbox(
                "Select Course", 
                course_options.keys(),
                key="unenroll_course_select"
            )
            course_id_unenroll = course_options[selected_course_unenroll]

            if st.button("Remove Student", key="unenroll_button"):
                success = manager.unenroll_student(student_id_unenroll, course_id_unenroll)
                if success:
                    st.success(f"{selected_student_unenroll.split(': ')[1]} removed from {selected_course_unenroll.split(': ')[1]}.")
                else:
                    st.error("Failed to remove student. Check console for details.")
        else:
            st.info(f"{selected_student_unenroll.split(': ')[1]} is not enrolled in any courses.")
    else:
        st.info("No students available for unenrollment.")