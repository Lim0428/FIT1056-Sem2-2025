import streamlit as st
from components.ui import apply_desktop_css, page_title
from services.data_store import list_tasks, complete_task

st.set_page_config(page_title="Tasks", page_icon="🗓️", layout="wide")
apply_desktop_css()

nurse_id = st.session_state["nurse_id"]
page_title("Daily Tasks", "Prioritized list with due times")

rows = list_tasks(nurse_id)
if not rows:
    st.info("No tasks assigned.")
else:
    for r in rows:
        with st.container():
            cols = st.columns([6, 2, 2])
            cols[0].markdown(f"**{r['title']}**  \nDue: {r['due']}  \nPatient: {r['patient_id']}")
            cols[1].write("High-risk" if r.get("high_risk") else "")
            if r.get("completed"):
                cols[2].button("Completed", disabled=True, key=r["id"] + "btn")
            else:
                if cols[2].button("Mark Complete", key=r["id"]):
                    try:
                        complete_task(r["id"], nurse_id)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        st.divider()
