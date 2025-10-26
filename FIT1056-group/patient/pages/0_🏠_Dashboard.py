# pages/0_🏠_Dashboard.py
from __future__ import annotations
import streamlit as st
from datetime import datetime

from components.ui import apply_theme, card, require_auth
from app.patient import PatientService
from app.auth import AuthService
from app.appointments import AppointmentService
from app.emergency import EmergencyService
from app.storage import read_db  # to peek 'room' from users if present (sec_q)

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")
apply_theme()
require_auth()

pid = st.session_state["auth_user"]
psvc = PatientService()
asvc = AppointmentService()
auth_svc = AuthService()
esvc = EmergencyService()

# ---------------- Header + One-click Emergency ----------------
left, right = st.columns([0.7, 0.3])
with left:
    st.markdown(
        """
        <div style="padding:14px 18px;border-radius:16px;background:linear-gradient(135deg,#1F2A44,#141A26);border:1px solid rgba(255,255,255,.08)">
          <div style="font-size:38px;font-weight:900;color:#fff;margin:0">Your Dashboard</div>
          <div style="opacity:.85;color:#CFE0FF">Snapshot of your health & activity</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ONE-CLICK EMERGENCY: no form — send immediately with name & room
    if st.button("🚨 Emergency Call Now", type="primary", use_container_width=True):
        prof = psvc.get(pid) or {}
        patient_name = prof.get("name", "")
        # Try to derive room: patient.profile['room'] (if you add), else users[pid]['sec_q'] if it looks like a room
        db = read_db()
        users = db.get("users") or {}
        u = users.get(pid) or {}
        candidate_room = ""
        # prefer explicit profile field if you add one later
        if prof.get("room"):
            candidate_room = str(prof.get("room"))
        else:
            sec_q = str(u.get("sec_q") or "")
            # if the security question looks like a room label, use it (e.g., "Room A")
            if sec_q.lower().startswith("room"):
                candidate_room = sec_q

        ok, call_id = esvc.raise_call(
            pid,
            patient_name=patient_name,
            room=candidate_room,
            priority="high",
            category="emergency",
            note="Auto SOS",
        )
        if ok:
            st.success(f"Emergency sent • ID: {call_id}")
        else:
            st.error(str(call_id))

# ---------------- Quick stats ----------------
with card("At a glance"):
    c1, c2, c3 = st.columns(3)
    with c1:
        prof = psvc.get(pid) or {}
        st.metric("Name", prof.get("name", "—"))
        st.caption(f"Patient ID: {pid}")
    with c2:
        appts = asvc.list_by_patient(pid) or []
        upcoming = [a for a in appts if a.get("dt","") >= datetime.now().isoformat()]
        st.metric("Upcoming appts", len(upcoming))
        if upcoming:
            st.caption(f"Next: {upcoming[0].get('dt','—')}")
    with c3:
        last = None
        hist = auth_svc.get_login_history(pid, limit=5)
        for e in hist:
            if e.get("status") == "success":
                last = e.get("ts"); break
        st.metric("Last login", last or "—")

# ---------------- Recent items ----------------
col_l, col_r = st.columns([0.6, 0.4])

with col_l:
    with card("Upcoming appointments"):
        if not appts:
            appts = asvc.list_by_patient(pid) or []
        if not appts:
            st.caption("No appointments yet.")
        else:
            for a in appts[:5]:
                st.write(f"• **{a.get('dt','—')}** — {a.get('note','') or 'Appointment'}")

with col_r:
    with card("Recent emergencies"):
        calls = esvc.list_by_patient(pid)
        if not calls:
            st.caption("No emergency calls.")
        else:
            for c in calls[:5]:
                st.write(
                    f"**{c.get('id','—')}** — {c.get('priority','').title()} / {c.get('category','')}  \n"
                    f"Room: {c.get('room','—') or '—'}  \n"
                    f"Status: {c.get('status','open').title()} &nbsp; • &nbsp; {c.get('ts','—')}"
                )
