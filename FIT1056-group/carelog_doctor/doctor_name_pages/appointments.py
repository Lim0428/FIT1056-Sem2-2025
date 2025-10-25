# doctor_name_pages/appointments.py
import streamlit as st
from datetime import datetime

def _parse(iso:str):
    try: return datetime.fromisoformat(str(iso).replace("Z",""))
    except: return None

def _hm(dt):
    h24,m=dt.hour, dt.minute
    h12 = 12 if (h24%12)==0 else (h24%12)
    ap = "AM" if h24<12 else "PM"
    return f"{h12}:{m:02d} {ap}"

def page_appointments(store):
    st.markdown("### Appointments")

    appts = store.list_all_appointments()
    appts.sort(key=lambda a: a.get("start",""))

    left, right = st.columns([5,7], gap="large")

    with left:
        st.markdown("**All appointments**")
        for a in appts:
            s=_parse(a.get("start","")); e=_parse(a.get("end",""))
            title=(a.get("reason") or "Consultation").title()
            sub = f"{s.strftime('%b %d, %Y')} • {_hm(s)}" + (f"–{_hm(e)}" if e else "")
            if st.button(f"{title}\n{sub}", key=f"appt_{a.get('id',id(a))}", use_container_width=True):
                st.session_state["selected_appt_id"] = a.get("id", None)
                st.rerun()

    with right:
        sel = st.session_state.get("selected_appt_id")
        row = None
        if sel:
            for a in appts:
                if a.get("id")==sel:
                    row=a; break
        row = row or (appts[0] if appts else None)
        if not row:
            st.info("No appointment selected.")
            return
        s=_parse(row.get("start","")); e=_parse(row.get("end",""))
        st.markdown("**Details**")
        st.write("Patient:", row.get("patient_name") or f"Patient #{row.get('patient_id','—')}")
        st.write("Reason:", row.get("reason","Consultation").title())
        st.write("Start:", s)
        st.write("End:", e or "—")
        st.write("Notes:", row.get("notes","—"))