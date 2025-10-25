# medical_staff/pages/4_✅_Tasks.py
from __future__ import annotations
from datetime import datetime, date
from typing import List

import streamlit as st
from components.ui import apply_theme, page_header, card  # no require_auth
from components.staff_shared import pick_staff_and_patient
from app.medical_staff import MedicalStaffService

# ---------- Page setup ----------
st.set_page_config(page_title="Tasks", page_icon="✅", layout="wide")
apply_theme()
svc = MedicalStaffService()

page_header("Tasks & Checklists", "Create tasks and mark them done.", "✅")

# ---------- Pick staff & patient ----------
# This also gets a Staff ID used in audit trails (no login/password required).
staff_id, patient = pick_staff_and_patient("task_pick")
if not patient:
    st.stop()
pid = patient["id"]

# ---------- Create task (full width) ----------
with card("Create task"):
    c1, c2 = st.columns([3, 1])
    with c1:
        title = st.text_input("Task title", "", key=f"task_title_{pid}")
    with c2:
        due = st.date_input("Due date", value=date.today(), key=f"task_due_{pid}")

    note = st.text_input("Note (optional)", "", key=f"task_note_{pid}")

    if st.button("➕ Add task", type="primary", key=f"task_add_{pid}"):
        if not title.strip():
            st.error("Please enter a task title.")
        else:
            # Store due date as ISO (midnight local)
            due_iso = datetime.combine(due, datetime.min.time()).isoformat()
            t = svc.add_task(staff_id, pid, title.strip(), due_iso, note.strip())
            st.success(f"Task {t.id} created.")
            st.rerun()  # refresh lists immediately

# ---------- Below: two columns ----------
# Left: Completed tasks (this patient)
# Right: Open tasks for this patient (moved from sidebar)
left, right = st.columns([2, 1], gap="large")

with left:
    with card("Completed tasks (this patient)"):
        all_tasks = svc.list_tasks(pid, include_done=True)
        done_list = [x for x in all_tasks if x.get("done")]
        if not done_list:
            st.caption("None yet.")
        else:
            for t in sorted(done_list, key=lambda x: x.get("due_date") or ""):
                when = t.get("due_date") or "n/a"
                st.write(f"✅ {t.get('title','(no title)')} — {when}")
                if t.get("note"):
                    st.caption(t["note"])

with right:
    with card("Open tasks for this patient"):
        open_tasks = svc.list_tasks(patient_id=pid, include_done=False)
        if not open_tasks:
            st.caption("No open tasks.")
        else:
            # Batch updates in a form to keep widget tree stable
            with st.form(f"open_tasks_form_{pid}", clear_on_submit=False):
                to_mark_done: List[str] = []

                for t in open_tasks:
                    label = f"{t.get('title','(no title)')}"
                    if t.get("due_date"):
                        label += f"  ·  Due: {t['due_date']}"
                    if t.get("note"):
                        label += f"  ·  {t['note']}"
                    if st.checkbox(label, key=f"chk_{t['id']}"):
                        to_mark_done.append(t["id"])

                submitted = st.form_submit_button(
                        "✅ Mark selected done",
                        type="primary",
                        use_container_width=True
                    )
                if submitted and to_mark_done:
                    who = st.session_state.get("auth_user", staff_id) or staff_id
                    for tid in to_mark_done:
                        svc.set_task_done(tid, True, who)
                    st.success(f"Marked {len(to_mark_done)} task(s) done.")
                    st.rerun()  # rerun once after all mutations
