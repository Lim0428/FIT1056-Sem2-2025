import streamlit as st

def teacher_page(manager):
    st.header("Teachers")

    # Show list of teachers
    teacher_data = [{"ID": t.id, "Name": t.name, "Speciality": t.speciality} for t in manager.teachers]
    st.dataframe(teacher_data)

    # Register new teacher
    st.subheader("Register New Teacher")
    with st.form("new_teacher_form"):
        name = st.text_input("Teacher Name")
        speciality = st.text_input("Speciality (e.g., Piano, Guitar, Violin)")
        submitted = st.form_submit_button("Register")
        if submitted and name:
            new_teacher = manager.register_new_teacher(name, speciality)
            st.success(f"Added {new_teacher.name} (ID: {new_teacher.id}, Speciality: {new_teacher.speciality})")