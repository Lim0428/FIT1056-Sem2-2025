# medical_staff/pages/4_✅_Tasks.py
from datetime import datetime, date
import streamlit as st
from components.ui import apply_theme, page_header, card
from components.staff_shared import pick_staff_and_patient
from app.medical_staff import MedicalStaffService

st.set_page_config(page_title="Tasks", page_icon="✅", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Tasks & Checklists", "Create and complete tasks.", "✅")

staff_id, patient = pick_staff_and_patient("task_pick")
if not patient:
    st.stop()
pid = patient["id"]

with card("Create task"):
    c1, c2 = st.columns([3,1])
    with c1: title = st.text_input("Task title", "", key=f"task_title_{pid}")
    with c2: due = st.date_input("Due date", value=date.today(), key=f"task_due_{pid}")
    note = st.text_input("Note (optional)", "", key=f"task_note_{pid}")
    if st.button("➕ Add task", type="primary", key=f"task_add_{pid}"):
        due_iso = datetime.combine(due, datetime.min.time()).isoformat()
        t = svc.add_task(staff_id, pid, title, due_iso, note)
        st.success(f"Task {t.id} created.")

with card("Open tasks"):
    tasks = svc.list_tasks(pid, include_done=False)
    if not tasks: st.caption("No open tasks.")
    else:
        for t in tasks:
            c1, c2 = st.columns([6,1])
            with c1:
                st.write(f"**{t['title']}** — due {t['due_date'] or 'n/a'}")
                if t.get("note"): st.caption(t["note"])
            with c2:
                if st.button("Done", key=f"task_done_{t['id']}"):
                    ok, msg = svc.set_task_done(t["id"], True, staff_id); st.success(msg) if ok else st.error(msg)

with card("Completed tasks"):
    done_list = [x for x in svc.list_tasks(pid, include_done=True) if x.get("done")]
    if not done_list: st.caption("None.")
    else:
        for t in done_list:
            st.write(f"✅ {t['title']} — {t['due_date'] or 'n/a'}")
