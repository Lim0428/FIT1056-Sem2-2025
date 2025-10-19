# gui/attendance_pages.py
import io
from collections import defaultdict
import streamlit as st
from gui.components import stat_cards

def _student_options(manager):
    """Map 'Alice Johnson (ID 1)' -> 1"""
    opts = {}
    for s in manager.students:
        label = f"{getattr(s, 'name', 'Student')} (ID {s.id})"
        opts[label] = s.id
    return opts

def _course_options(manager):
    """Map '101 — Beginner Piano' -> course_id"""
    opts = {}
    for c in manager.courses:
        label = f"{c.id} — {getattr(c, 'name', 'Course')}"
        opts[label] = c.id
    return opts

def _export_download_button(path, label="Download CSV"):
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    st.download_button(label=label,
                       data=io.BytesIO(data.encode("utf-8")),
                       file_name=path.split("/")[-1],
                       mime="text/csv")

def show_attendance_page(manager):
    st.header("Check-in Student")

    stat_cards([
        {"label": "Students", "value": len(manager.students), "help": "Registered", "icon": "👩‍🎓"},
        {"label": "Checked In (All Time)", "value": len(getattr(manager, "attendance_log", []) or []), "help": "Total events", "icon": "✅"},
        {"label": "Courses", "value": len(manager.courses), "help": "Active", "icon": "🎵"},
    ])
    st.write("")
    # ---------------------- Check-in form ----------------------
    colA, colB = st.columns(2)
    with colA:
        student_map = _student_options(manager)
        if not student_map:
            st.info("No students available.")
            return
        student_label = st.selectbox("Student", list(student_map.keys()), key="att_student")
        student_id = student_map[student_label]

    with colB:
        course_map = _course_options(manager)
        if not course_map:
            st.info("No courses available.")
            return
        course_label = st.selectbox("Course", list(course_map.keys()), key="att_course")
        course_id = course_map[course_label]

    # Precheck (warn staff if not eligible right now)
    eligible_now = set(manager.eligible_courses_for_student_now(student_id, window_minutes=90))
    if course_id not in eligible_now:
        st.warning("Heads up: this course is not currently in an allowable check-in window for today.")


    if st.button("Check-in"):
        ok = manager.check_in(student_id, course_id)
        if ok:
            st.success("Check-in recorded.")
        else:
            st.error("Check-in failed. Ensure the student is enrolled in the course.")

    st.divider()

    # ---------------------- Attendance Report (Summary) ----------------------
    st.header("Attendance Report")

    log = getattr(manager, "attendance_log", []) or []
    if log:
        # Aggregate by (student_name, course_name)
        counts = defaultdict(int)
        for a in log:
            sid = a.get("student_id")
            cid = a.get("course_id")
            s = manager.find_student_by_id(sid)
            c = manager.find_course_by_id(cid)
            if not s or not c:
                continue
            counts[(s.name, c.name)] += 1

        summary_rows = [
            {"Student": sname, "Course": cname, "Check-ins": n}
            for (sname, cname), n in counts.items()
        ]
        summary_rows.sort(key=lambda r: (r["Student"], r["Course"]))

        st.subheader("Summary by Student and Course")
        st.dataframe(summary_rows, use_container_width=True)

        # ---------------------- Raw Log ----------------------
        st.subheader("Raw Attendance Log")
        raw_rows = []
        for a in log:
            sid = a.get("student_id")
            cid = a.get("course_id")
            s = manager.find_student_by_id(sid)
            c = manager.find_course_by_id(cid)
            raw_rows.append({
                "Student ID": sid,
                "Student": s.name if s else "",
                "Course ID": cid,
                "Course": c.name if c else "",
                "Timestamp": a.get("timestamp", ""),
            })
        st.dataframe(raw_rows, use_container_width=True)

        # ---------------------- Export Button ----------------------
        if st.button("Export Attendance CSV"):
            path = manager.export_report("attendance", "exports/attendance.csv")
            _export_download_button(path, label="Download attendance.csv")
            st.success("Attendance report generated.")
    else:
        st.info("No attendance records yet.")
