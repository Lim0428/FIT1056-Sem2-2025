import streamlit as st

def show_student_management_page(manager):
    """Renders all components for the student management page."""
    st.header("Student Management")

    st.subheader("Find a Student")

    st.subheader("Register New Student")

    instruments = list({c.instrument for c in manager.courses})
    if not instruments:
        st.warning("No courses available yet. Please create courses first.")
        return
    
    with st.form("registration_form"):
        reg_name = st.text_input("New Student Name")
        reg_instrument = st.text_input("First Instrument")
        submitted = st.form_submit_button("Register Student")
        
        if submitted:
            # This call now works because we implemented the method in PST3.
            # TODO: Add a check for blank name/instrument.
            if not reg_name:
                st.warning("Please enter a student name.")
            elif not reg_instrument:
                st.warning("Please enter an instrument.")
            else:
                new_student = manager.register_new_student(reg_name, reg_instrument)
                if new_student:
                    st.success(f"Successfully registered {reg_name}!")
                    # You can use st.balloons() for extra flair.
                else:
                    st.error(f"Could not register student. A teacher for {reg_instrument} might not be available.")

    st.subheader("All Students")
    students = manager.get_all_students()
    if students:
        st.table(students)
    else:
        st.info("No students registered yet.")
        