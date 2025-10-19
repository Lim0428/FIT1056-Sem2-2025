# gui/register_student.py
import streamlit as st

def show_register_student(manager):
    st.subheader("👩‍🎓 Register New Student")

    with st.form("register_student_form", clear_on_submit=True):
        name = st.text_input("Full name")
        instrument = st.text_input("Instrument", placeholder="e.g., Piano, Violin, Guitar")
        submitted = st.form_submit_button("Register Student")

    if submitted:
        if not name or not instrument:
            st.warning("Please enter both name and instrument.")
            return
        try:
            stu = manager.register_new_student(name.strip(), instrument.strip())
            st.success(f"Student created: ID **{stu.id}** — {stu.name} ({instrument})")
            # quick facts
            st.caption("Tip: Use **Student Enrollment** to add this student to a course.")
        except Exception as e:
            st.error(f"Could not register student: {e}")

    st.divider()

    # Recent students (quick glance)
    if manager.students:
        latest = sorted(manager.students, key=lambda s: s.id, reverse=True)[:10]
        rows = [
            {
                "ID": s.id,
                "Name": getattr(s, "name", ""),
                "Instrument": getattr(s, "instrument", "N/A"),
                "Balance": getattr(s, "balance", 0.0),
                "Enrolled": len(getattr(s, "enrolled_course_ids", []) or []),
            }
            for s in latest
        ]
        st.write("Recent students")
        st.dataframe(rows, use_container_width=True)
