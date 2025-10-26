# pages/2_🧾_Session_Notes.py
import streamlit as st
from counselor_name_components.ui import apply_theme, top_nav, require_auth
from counselor_name_components.forms import session_note_form, render_quick_assessments
from counselor_name_components.tables import notes_table
from counselor_name_app.services.patients import PatientService
from counselor_name_app.services.notes import NotesService
from counselor_name_app.services.consent import ConsentService

st.set_page_config(page_title="Session Notes", page_icon="🧾", layout="wide")
apply_theme(); require_auth(); top_nav("Session Notes")

me = st.session_state["auth_user"]
ps = PatientService()
consent = ConsentService()
notes = NotesService()

patients = ps.list_assigned(me)
if not patients:
    st.info("No assigned patients yet."); st.stop()

pid = st.selectbox("Patient", options=[p["id"] for p in patients],
                   format_func=lambda x: next(p['name'] for p in patients if p['id']==x))

if not consent.allowed(me, pid):
    with st.warning("Consent required. You may use break-glass with reason."):
        reason = st.text_input("Reason for break-glass access")
        if st.button("Break-glass (audited)"):
            if reason.strip():
                consent.break_glass(me, pid, reason); st.success("Temporary access granted."); st.rerun()
            else:
                st.error("Reason is required.")
    st.stop()

st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

left, right = st.columns([1.8, 1])

with left:
    tpl = st.segmented_control("Template", options=["SOAP","DARE"], default="SOAP")
    form = session_note_form(tpl)
    if st.button("Save Session Note", type="primary"):
        created = notes.create(pid, me, tpl, form["title"], form["content"])
        st.success(f"Saved note {created['id']}"); st.rerun()

with right:
    render_quick_assessments(pid, me)

st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)
notes_table(notes.list_notes(pid))
