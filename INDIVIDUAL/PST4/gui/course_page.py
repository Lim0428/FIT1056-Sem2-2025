import streamlit as st

def course_page(manager):
    st.header("Courses")

    # Show list of courses
    st.subheader("Current Courses")
    course_data = [
        {"ID": c.id, "Name": c.name, "Instrument": c.instrument,
        "Teacher": manager.find_teacher_by_id(c.teacher_id).name if manager.find_teacher_by_id(c.teacher_id) else "Unknown",
        "Fee": c.fee}
        for c in manager.courses
    ]
    st.dataframe(course_data)

    st.subheader("Set Course Fee")
    with st.form("fee_form"):
        cid = st.selectbox("Select Course", [c.id for c in manager.courses])
        fee = st.number_input("New Fee", min_value=0.0, step=10.0)
        submitted = st.form_submit_button("Update Fee")
        if submitted:
            manager.set_course_fee(cid, fee)
            st.success(f"Updated course {cid} fee to {fee}")

    st.subheader("Add New Course")
    with st.form("new_course_form"):
        name = st.text_input("Course Name")
        instrument = st.text_input("Instrument (e.g., Piano, Guitar, Violin)")
        teacher = st.selectbox("Assign Teacher", manager.teachers, format_func=lambda t: f"{t.name} (ID: {t.id})")
        fee = st.number_input("Course Fee", min_value=0.0, step=10.0)
        submitted = st.form_submit_button("Add Course")
        if submitted and name:
            new_course = manager.add_course(name, instrument, teacher.id, fee)
            st.success(f"Added course {new_course.name} (ID: {new_course.id}) with teacher {teacher.name}")