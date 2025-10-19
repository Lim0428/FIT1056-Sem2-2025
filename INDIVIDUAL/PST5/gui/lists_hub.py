# gui/lists_hub.py
import streamlit as st
import io, csv

def _csv_download(label, rows, headers, filename):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=headers)
    w.writeheader()
    w.writerows([{h: r.get(h, "") for h in headers} for r in rows])
    st.download_button(
        label=label,
        data=buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )

def _qfilter(rows, q):
    if not q:
        return rows
    q = q.strip().lower()
    out = []
    for r in rows:
        # match on any field
        if any(q in str(v).lower() for v in r.values()):
            out.append(r)
    return out

def _students_rows(manager):
    rows = []
    for s in manager.students:
        rows.append({
            "ID": s.id,
            "Name": getattr(s, "name", ""),
            "Instrument": getattr(s, "instrument", "N/A"),
            "Balance": getattr(s, "balance", 0.0),
            "Enrolled Count": len(getattr(s, "enrolled_course_ids", []) or []),
        })
    return rows

def _teachers_rows(manager):
    rows = []
    for t in manager.teachers:
        rows.append({
            "ID": t.id,
            "Name": getattr(t, "name", ""),
            "Speciality": getattr(t, "speciality", "Unknown"),
        })
    return rows

def _courses_rows(manager):
    rows = []
    for c in manager.courses:
        teacher = manager.find_teacher_by_id(c.teacher_id)
        rows.append({
            "ID": c.id,
            "Course": getattr(c, "name", ""),
            "Instrument": getattr(c, "instrument", ""),
            "Teacher": teacher.name if teacher else "Unknown",
            "Fee": getattr(c, "fee", 0.0),
            "Students": len(getattr(c, "enrolled_student_ids", []) or []),
            "Lessons": len(getattr(c, "lessons", []) or []),
        })
    return rows

def show_lists_hub(manager):
    st.subheader("📚 Directory")

    tabs = st.tabs(["👩‍🎓 Students", "👨‍🏫 Teachers", "🎼 Courses"])

    # --- Students
    with tabs[0]:
        rows = _students_rows(manager)
        c1, c2 = st.columns([2,1])
        with c1:
            q = st.text_input("Search students", placeholder="Name, instrument, ID…")
        with c2:
            st.caption(f"Total: **{len(rows)}**")
        filtered = _qfilter(rows, q)
        st.dataframe(filtered, use_container_width=True)
        _csv_download("Download students CSV", filtered,
                      headers=["ID", "Name", "Instrument", "Balance", "Enrolled Count"],
                      filename="students.csv")

    # --- Teachers
    with tabs[1]:
        rows = _teachers_rows(manager)
        c1, c2 = st.columns([2,1])
        with c1:
            q = st.text_input("Search teachers", key="q_teachers", placeholder="Name, speciality, ID…")
        with c2:
            st.caption(f"Total: **{len(rows)}**")
        filtered = _qfilter(rows, q)
        st.dataframe(filtered, use_container_width=True)
        _csv_download("Download teachers CSV", filtered,
                      headers=["ID", "Name", "Speciality"],
                      filename="teachers.csv")

    # --- Courses
    with tabs[2]:
        rows = _courses_rows(manager)
        c1, c2 = st.columns([2,1])
        with c1:
            q = st.text_input("Search courses", key="q_courses", placeholder="Course, instrument, teacher…")
        with c2:
            st.caption(f"Total: **{len(rows)}**")
        filtered = _qfilter(rows, q)
        st.dataframe(filtered, use_container_width=True)
        _csv_download("Download courses CSV", filtered,
                      headers=["ID", "Course", "Instrument", "Teacher", "Fee", "Students", "Lessons"],
                      filename="courses.csv")
