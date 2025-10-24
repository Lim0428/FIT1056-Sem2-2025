import streamlit as st
from components.ui import apply_desktop_css, page_title, card
from services.data_store import list_assigned_patients, check_access, list_timeline

st.set_page_config(page_title="Patients • Nurse", page_icon="👤", layout="wide")
apply_desktop_css()

nurse_id = st.session_state["nurse_id"]
page_title("Patients", "Assigned to you")

rows = list_assigned_patients(nurse_id)
if not rows:
    st.info("No patients assigned yet.")
else:
    names = {p["id"]: f'{p["name"]} • {p.get("gender","-")} • {p.get("age","-")}y' for p in rows}
    pid = st.selectbox("Select a patient", list(names.keys()), format_func=lambda k: names[k], index=0)
    st.divider()
    if pid and check_access(nurse_id, pid):
        st.success("Access granted (assignment check passed).")
        st.subheader("Timeline")
        cols = st.columns(2)
        left, right = cols[0], cols[1]
        items = list_timeline(pid)[:30]
        for idx, item in enumerate(items):
            kind = item["_kind"].upper()
            body = ""
            if kind == "MAR":
                body = f'{item["drug"]} {item["dose"]} via {item["route"]}'
            elif kind == "VITALS":
                body = f"<pre>{item['values']}</pre>"
            else:
                body = item["text"]
            (left if idx % 2 == 0 else right).markdown(
                f"<div class='cl-card'><h4>{kind}</h4><div style='opacity:.8'>{item['ts']}</div><div style='margin-top:6px'>{body}</div></div>",
                unsafe_allow_html=True,
            )
    else:
        st.error("Access blocked (not assigned). Attempt logged.")
