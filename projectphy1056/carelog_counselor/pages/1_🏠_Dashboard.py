# pages/1_🏠_Dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

from counselor_name_components.ui import apply_theme, top_nav, require_auth
from counselor_name_app.repository import Repo
from counselor_name_app.services.patients import PatientService
from counselor_name_app.services.appointments import AppointmentService
from counselor_name_app.services.messaging import MessagingService
from streamlit.components.v1 import html as html_embed  # for a single HTML block

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")
apply_theme()
require_auth(); top_nav("Dashboard")

# ---------- helpers ----------
def _to_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso)

def _duration_hours(s: datetime, e: datetime) -> float:
    dur = (e - s).total_seconds() / 3600.0
    return max(dur, 0.5) if dur <= 0 else dur

def _appt_df(appts: list[dict]) -> pd.DataFrame:
    if not appts:
        return pd.DataFrame(columns=["id","patient_id","start","end","kind","status","date","duration_hrs"])
    rows = []
    for a in appts:
        s = _to_dt(a["start"]); e = _to_dt(a["end"])
        rows.append({
            "id": a["id"], "patient_id": a["patient_id"],
            "start": s, "end": e, "kind": a.get("kind","Individual"),
            "status": a.get("status","Booked"), "date": s.date(),
            "duration_hrs": _duration_hours(s, e)
        })
    return pd.DataFrame(rows)

# ---------- data ----------
me = st.session_state["auth_user"]
repo = Repo(); db = repo.read()
ps = PatientService(); asvc = AppointmentService(); msvc = MessagingService()

patients = ps.list_assigned(me)
appts_me = asvc.list_for_counselor(me)
threads = msvc.list_threads(me)
df_appt = _appt_df(appts_me)
today = date.today()

# ---------- top summary ----------
def pill(label: str, value, help_text: str = ""):
    st.markdown(
        f"""
        <div class="k-card" style="padding:12px; display:flex; align-items:center; gap:12px;">
            <div style="font-weight:700; font-size:28px; line-height:1;">{value}</div>
            <div>
                <div style="opacity:.85; font-weight:600;">{label}</div>
                <div class="muted" style="font-size:12px;">{help_text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

colA, colB, colC, colD = st.columns(4)
with colA:
    pill("Patients", len(patients), "Assigned to you")
with colB:
    appts_today = df_appt[df_appt["date"] == today] if not df_appt.empty else pd.DataFrame()
    pill("Appointments Today", 0 if appts_today.empty else len(appts_today))
with colC:
    pill("Active Threads", len(threads), "Messages overview")
with colD:
    next7 = 0 if df_appt.empty else len(df_appt[(df_appt["start"] >= datetime.now()) & (df_appt["start"] <= datetime.now()+timedelta(days=7))])
    pill("Next 7d Appointments", next7)

st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

# ---------- two-column layout ----------
left, right = st.columns([1.8, 1.2])

# LEFT: caseload + duty hours
with left:
    st.markdown("#### 🗂️ Caseload & Alerts")
    caseload = {
        "Total assigned": len(patients),
        "With risk flags": sum(1 for p in patients if p.get("risk_flags")),
        "With safety plan": sum(1 for pid in db.get("safety_plans", {}).keys() if any(p["id"]==pid for p in patients)),
        "Seen this month": 0 if df_appt.empty else len({r["patient_id"] for _, r in df_appt[df_appt["date"]>=today.replace(day=1)].iterrows()}),
    }
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total assigned", caseload["Total assigned"])
        st.metric("With safety plan", caseload["With safety plan"])
    with c2:
        st.metric("With risk flags", caseload["With risk flags"])
        st.metric("Seen this month", caseload["Seen this month"])

    risky = [p for p in patients if p.get("risk_flags")]
    st.markdown("##### ⚠️ Risk Alerts")
    if not risky:
        st.info("No current risk flags.")
    else:
        for p in risky:
            st.markdown(
                f"""
                <div class="k-card" style="padding:10px; margin-bottom:8px;">
                    <b>{p['name']}</b> · {p['id']}<br/>
                    <span class="muted">Flags: {", ".join(p.get("risk_flags", []))}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("##### ⏱ Duty Hour (Next 7 days)")
    if df_appt.empty:
        st.info("No appointments to compute duty hours.")
    else:
        start = today
        mask = (df_appt["date"] >= start) & (df_appt["date"] <= today + timedelta(days=6))
        duty = (df_appt.loc[mask]
                .groupby("date", as_index=False)["duration_hrs"].sum()
                .rename(columns={"date": "Day", "duration_hrs": "Hours"}))
        days = [start + timedelta(days=i) for i in range(7)]
        full = pd.DataFrame({"Day": days}).merge(duty, on="Day", how="left").fillna({"Hours": 0.0})
        full["Label"] = pd.to_datetime(full["Day"], errors="coerce").dt.strftime("%b %d").fillna(full["Day"].astype(str))
        st.line_chart(full.set_index("Label")["Hours"])

# RIGHT: today list + fixed chat (single HTML block)
with right:
    st.markdown("#### 📅 Today’s Appointments")
    if appts_today.empty:
        st.info("No appointments today.")
    else:
        appts_today = appts_today.sort_values("start")
        for _, r in appts_today.iterrows():
            st.markdown(
                f"""
                <div class="k-card" style="padding:10px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between;">
                        <div><b>{r['patient_id']}</b> · {r['kind']}</div>
                        <div class="muted">{r['start'].strftime('%I:%M %p')} – {r['end'].strftime('%I:%M %p')}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ---------- Team Chat ----------
    st.markdown("#### 💬 Team Chat")

    role = st.selectbox("Talk to", ["patient","admin","medstaff","nurse","doctor"])
    if role == "patient":
        choices = [{"id": p["id"], "name": p["name"]} for p in patients]
    else:
        choices = [{"id": u["id"], "name": u["name"]} for u in msvc.users_by_role(role)]

    if not choices:
        st.info("No available recipients for this role.")
    else:
        sel = st.selectbox(
            "Recipient",
            options=[c["id"] for c in choices],
            format_func=lambda x: next(c["name"] for c in choices if c["id"]==x)
        )
        members = [me, sel]
        title = f"{role}:{sel}"

        threads_me = msvc.list_threads(me)
        existing = next((t["id"] for t in threads_me if set(t.get("members", [])) == set(members)), None)
        thread_id = existing or (msvc.create_or_get_thread(title, members) if hasattr(msvc, "create_or_get_thread") else msvc.post(None, members, me, "Hello")["thread_id"])
        active = next((t for t in msvc.list_threads(me) if t["id"] == thread_id), None)

        # ---- Build ONE HTML string for the chat (fixed 420px height) ----
        css = """
        <style>
          .chat-pane { background:#111b27; border:1px solid #1e2a3a; border-radius:16px; padding:8px; }
          .chat-scroll { height:420px; overflow-y:auto; padding:6px 8px 2px 8px; }
          .row { display:flex; margin:8px 0; }
          .row.me   { justify-content:flex-end; }
          .row.them { justify-content:flex-start; }
          .bubble { max-width:78%; padding:12px 14px; border-radius:16px; line-height:1.45; }
          .bubble.me   { background:#17314d; border:1px solid #27425f; border-bottom-right-radius:6px; color:#e7eef8; }
          .bubble.them { background:#162332; border:1px solid #263244; border-bottom-left-radius:6px; color:#e7eef8; }
          .bubble.sys  { background:#221a1a; border:1px dashed #3b2a2a; color:#f6d7d7; max-width:60%;
                         border-radius:10px; margin:0 auto; }
          .meta { font-size:11px; opacity:.75; padding-top:4px; text-align:right; }
        </style>
        """
        rows = []
        if active:
            for msg in active.get("items", [])[-200:]:
                who = "You" if msg["by"] == me else (msvc.get_user(msg["by"]) or {"name": msg["by"]})["name"] if hasattr(msvc, "get_user") else ("You" if msg["by"]==me else msg["by"])
                cls_row = "me" if msg["by"] == me else ("them" if msg["by"] != "system" else "")
                cls_bubble = "me" if msg["by"] == me else ("them" if msg["by"] != "system" else "sys")
                rows.append(
                    f"""
                    <div class="row {cls_row}">
                      <div class="bubble {cls_bubble}">
                        <div>{msg['text']}</div>
                        <div class="meta">{who} · {msg['ts']}</div>
                      </div>
                    </div>
                    """
                )
        chat_html = css + f"""<div class="chat-pane"><div class="chat-scroll">{''.join(rows)}</div></div>"""
        html_embed(chat_html, height=460, scrolling=False)

        # compose
        text = st.text_area("Type your message…", key=f"dash_msg_{thread_id}", height=110, label_visibility="collapsed")
        csend, csim = st.columns([1,1])
        if csend.button("Send", type="primary", key=f"dash_send_{thread_id}"):
            if text.strip():
                if hasattr(msvc, "create_or_get_thread"):
                    msvc.post(thread_id, members, me, text.strip(), title=title)
                else:
                    msvc.post(thread_id, members, me, text.strip())
                st.rerun()
        if csim.button("Simulate reply from selected user", key=f"dash_sim_{thread_id}"):
            if hasattr(msvc, "create_or_get_thread"):
                msvc.post(thread_id, members, sel, "Acknowledged. Thanks for the update!", title=title)
            else:
                msvc.post(thread_id, members, sel, "Acknowledged. Thanks for the update!")
            st.rerun()

st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

# ---------- Appointment History (this month) ----------
st.markdown("#### 📜 Appointment History (This Month)")
if df_appt.empty:
    st.info("No appointment history yet.")
else:
    start_month = today.replace(day=1)
    hist = df_appt[df_appt["date"] >= start_month].sort_values("start", ascending=False)
    cols = st.columns(2)
    for i, (_, r) in enumerate(hist.iterrows()):
        with cols[i % 2]:
            st.markdown(
                f"""
                <div class="k-card" style="padding:10px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between;">
                        <div><b>{r['date'].strftime('%b %d')}</b> · {r['patient_id']} · {r['kind']}</div>
                        <div class="muted">{r['start'].strftime('%I:%M %p')}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
