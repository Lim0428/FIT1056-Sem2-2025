import streamlit as st
from components.ui import apply_desktop_css, page_title
from services.data_store import list_notifications, ack_notification

st.set_page_config(page_title="Notifications", page_icon="🔔", layout="wide")
apply_desktop_css()

nurse_id = st.session_state["nurse_id"]
page_title("Notifications", "Doctor updates and patient calls")

rows = list_notifications(nurse_id)
if not rows:
    st.success("No new notifications.")
else:
    for n in rows:
        with st.container():
            st.markdown(f"**{n['title']}**  \n{n['ts']}  \n{n['body']}")
            if n.get("ack"):
                st.info("Acknowledged")
            else:
                if st.button("Acknowledge", key=n["id"]):
                    try:
                        ack_notification(n["id"], nurse_id)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        st.divider()
