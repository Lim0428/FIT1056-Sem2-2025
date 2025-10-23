import streamlit as st
from doctor_name_services.messaging import (
    list_threads, get_thread, add_message, mark_resolved
)
from doctor_name_components.tables import table_messages
# example: make a red button for destructive action

with st.container():
    st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
    if st.button("Delete", use_container_width=True):
        ...
    st.markdown('</div>', unsafe_allow_html=True)

def page_messages(store):
    st.subheader("Secure Messaging (Mark Resolved)")

    threads = list_threads(store)
    flat = [{"thread_id": t["id"], "patient_id": t["patient_id"], "status": t["status"], "updated_at": t["updated_at"]} for t in threads]
    table_messages(flat)

    tid = st.text_input("Open thread by ID")
    if tid:
        thr = get_thread(store, tid)
        if not thr:
            st.error("Thread not found or not permitted.")
            return
        st.markdown(f"**Thread #{thr['id']}** • Patient #{thr['patient_id']} • Status: {thr['status']}")
        for m in thr["messages"]:
            who = "Doctor" if m["sender_role"] == "doctor" else "Patient"
            st.write(f"{who} @ {m['timestamp']}: {m['text']}")
        st.divider()

        with st.form("reply_form"):
            txt = st.text_area("Reply")
            sent = st.form_submit_button("Send", use_container_width=True)
            if st.button("Mark Resolved", use_container_width=True):
    
                add_message(store, thr["id"], "doctor", txt.strip())
                st.success("Sent.")
                st.rerun()

        if thr["status"] != "resolved":
            if st.button("Mark Resolved"):
                mark_resolved(store, thr["id"])
                st.success("Thread marked resolved.")
                st.rerun()
