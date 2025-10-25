# doctor_name_pages/encounters.py
import streamlit as st
from datetime import datetime
from doctor_name_services.data_store import FILES
import json

def _read(path, default):
    try:
        with open(path,"r",encoding="utf-8") as f: return json.load(f)
    except: return default

def _parse(s): 
    try: return datetime.fromisoformat(str(s).replace("Z",""))
    except: return None

def page_encounters(store=None):
    st.markdown("### Encounters")

    encs = _read(FILES["encounters"], [])
    if isinstance(encs, dict) and isinstance(encs.get("encounters"), list):
        encs = encs["encounters"]
    encs = [e for e in encs if isinstance(e, dict)]
    encs.sort(key=lambda e: _parse(e.get("timestamp","") or e.get("created_at","")) or datetime.min, reverse=True)

    kind = st.radio("Type", ["All", "Consultation", "Treatment", "Follow-up"], horizontal=True)
    if kind != "All":
        encs = [e for e in encs if (e.get("type") or "").lower() == kind.lower()]

    q = st.text_input("Search", placeholder="Search by title or notes…").strip().lower()
    if q:
        encs = [e for e in encs if q in (e.get("title","")+ " "+ e.get("notes","")).lower()]

    left, right = st.columns([5,7], gap="large")
    with left:
        st.markdown("**List**")
        for e in encs:
            t = e.get("title") or e.get("type") or "Encounter"
            w = _parse(e.get("timestamp","") or e.get("created_at",""))
            sub = w.strftime("%b %d, %Y") if w else "—"
            if st.button(f"{t}\n{sub}", key=f"enc_{e.get('id',id(e))}", use_container_width=True):
                st.session_state["selected_enc_id"] = e.get("id")
                st.rerun()

    with right:
        sel = st.session_state.get("selected_enc_id")
        row = None
        if sel:
            for e in encs:
                if e.get("id")==sel:
                    row=e; break
        row = row or (encs[0] if encs else None)
        if not row:
            st.info("No encounter selected."); return
        st.markdown("**Details**")
        st.write("Title:", row.get("title") or row.get("type") or "Encounter")
        st.write("Patient:", row.get("patient_name") or f"Patient #{row.get('patient_id','—')}")
        st.write("Timestamp:", row.get("timestamp") or row.get("created_at") or "—")
        st.write("Notes:", row.get("notes","—"))
        st.write("Versions:", row.get("versions", []))
