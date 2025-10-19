# gui/lesson_pages.py
import streamlit as st
import pandas as pd

def _get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def _rerun():
    """Streamlit refresh that works on new/old versions."""
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()  # older Streamlit
        except Exception:
            pass

def show_lesson_page(manager):
    st.header("Lesson Management")

    # ---------------- Build course -> lessons map ----------------
    course_map = {}
    courses = getattr(manager, "courses", []) or []
    for c in courses:
        cid = int(_get(c, "id"))
        cname = _get(c, "name", f"Course {cid}")
        tname = None
        tid = _get(c, "teacher_id", None)
        if tid is not None and hasattr(manager, "find_teacher_by_id"):
            t = manager.find_teacher_by_id(tid)
            tname = _get(t, "name", None) if t else None

        lessons = _get(c, "lessons", []) or []
        norm = []
        for L in lessons:
            lid = _get(L, "lesson_id", _get(L, "id", None))
            if lid is None:
                continue
            norm.append({
                "lesson_id": int(lid),
                "day": _get(L, "day", "TBD"),
                "start_time": _get(L, "start_time", _get(L, "time", "TBD")),
                "room": _get(L, "room", "TBD"),
                "cancelled": bool(_get(L, "cancelled", False)),
            })
        course_map[cid] = {"name": cname, "teacher_name": tname, "lessons": sorted(norm, key=lambda x: x["lesson_id"])}

    # ---------------- All Scheduled Lessons ----------------
    st.subheader("All Scheduled Lessons")
    rows = []
    for cid, meta in course_map.items():
        for L in meta["lessons"]:
            rows.append({
                "Lesson ID": L["lesson_id"],
                "Course": meta["name"],
                "Teacher": meta["teacher_name"] or "Unknown",
                "Day": L["day"],
                "Start Time": L["start_time"],
                "Room": L["room"],
                "Cancelled": "Yes" if L["cancelled"] else "No",
            })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No lessons scheduled yet.")

    # ---------------- Add Lesson ----------------
    st.subheader("Add Lesson")
    with st.form("lesson_add_form"):
        add_course_id = st.selectbox(
            "Course",
            options=sorted(course_map.keys()),
            format_func=lambda cid: f"{cid} — {course_map[cid]['name']}",
            key="add_course_id",
        )
        add_day = st.text_input("Day (e.g. Monday)", key="add_day")
        add_time = st.text_input("Start Time (HH:MM)", key="add_time")
        add_room = st.text_input("Room", key="add_room")
        add_submit = st.form_submit_button("Add Lesson")
        if add_submit:
            new_lesson = manager.add_lesson(int(add_course_id), add_day, add_time, add_room)
            st.success(f"Added Lesson {new_lesson['lesson_id']} to Course {add_course_id}.")
            _rerun()

    st.divider()

    # ---------------- Cancel Lesson (form + explicit results) ----------------
    st.subheader("Cancel Lesson")

    if not course_map:
        st.info("No courses available.")
    else:
        # 1) Pick course
        sel_cancel_course = st.selectbox(
            "Course",
            options=sorted(course_map.keys()),
            format_func=lambda cid: f"{cid} — {course_map[cid]['name']}",
            key="cancel_course_id",
        )

        # 2) Build lesson list for that exact course
        lessons_for_course = course_map.get(int(sel_cancel_course), {}).get("lessons", [])
        lesson_id_options = [L["lesson_id"] for L in lessons_for_course]

        # 3) Reset stale selection when course changes
        last_course_key = "__last_cancel_course__"
        if st.session_state.get(last_course_key) != sel_cancel_course:
            # zap any old selection so Streamlit doesn't reuse 1–4 from another course
            st.session_state.pop(f"cancel_lesson_id_{st.session_state.get(last_course_key)}", None)
            st.session_state[last_course_key] = sel_cancel_course

        # 4) Use a UNIQUE KEY PER COURSE for the lesson selectbox
        lesson_key = f"cancel_lesson_id_{sel_cancel_course}"

        with st.form("cancel_lesson_form"):
            sel_cancel_lesson = st.selectbox(
                "Lesson",
                options=lesson_id_options,
                key=lesson_key,
                disabled=not lesson_id_options,
            )
            cancel_reason = st.text_input(
                "Reason for cancellation",
                value="Cancelled via UI",
                key=f"cancel_reason_{sel_cancel_course}",
            )
            submitted = st.form_submit_button("Cancel this lesson", disabled=not lesson_id_options)

        if submitted:
            try:
                ok = bool(manager.cancel_lesson(int(sel_cancel_course), int(sel_cancel_lesson), cancel_reason or ""))
            except TypeError:
                # Fallback if your manager has a different signature
                ok = bool(manager.cancel_lesson(int(sel_cancel_lesson)))
            except Exception as e:
                st.error(f"Cancel failed: {e}")
                ok = False

            if ok:
                st.success(f"Lesson {sel_cancel_lesson} cancelled.")
                try:
                    st.rerun()
                except AttributeError:
                    try: st.experimental_rerun()
                    except Exception: pass
            else:
                st.error("Manager did not confirm cancellation. If the table above doesn’t change, "
                        "your cancel_lesson may not update course.lessons.")


    # ---------------- Reschedule Lesson ----------------
    st.subheader("Reschedule Lesson")
    with st.form("lesson_reschedule_form"):
        sel_res_course = st.selectbox(
            "Course (Reschedule)",
            options=sorted(course_map.keys()),
            format_func=lambda cid: f"{cid} — {course_map[cid]['name']}",
            key="res_course_id",
        )
        res_lesson_ids = [L["lesson_id"] for L in course_map.get(int(sel_res_course), {}).get("lessons", [])]
        sel_res_lesson = st.selectbox("Lesson ID", options=res_lesson_ids, key=f"res_lesson_id_for_{sel_res_course}", disabled=not res_lesson_ids)
        new_day = st.text_input("New Day", key="res_new_day")
        new_time = st.text_input("New Time", key="res_new_time")
        new_room = st.text_input("New Room", key="res_new_room")
        res_submit = st.form_submit_button("Reschedule")
        if res_submit:
            manager.reschedule_lesson(int(sel_res_course), int(sel_res_lesson), new_day, new_time, new_room)
            st.success("Lesson rescheduled.")
            _rerun()
