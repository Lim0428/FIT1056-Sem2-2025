# medical_staff/pages/0_🏠_Dashboard.py
from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
import altair as alt

from components.ui import apply_theme, page_header, card, set_altair_dark_theme
from app.medical_staff_service import MedicalStaffService


# -------------------------- Pretty attention table --------------------------
def render_attention_table(
    svc: MedicalStaffService,
    *,
    staff_id: str | None = None,
    only_my: bool = False,
    top_n: int = 10,
) -> None:
    """Beautiful table: Patient (Name — ID) + Open tasks (progress bar)."""
    import streamlit as st
    import pandas as pd
    from components.ui import card

    patients = svc.list_patients(assigned_to=(staff_id if only_my else None))
    rows = []
    for p in patients:
        pid = p.get("id", "")
        name = p.get("name", "(no name)")
        open_cnt = len(svc.list_tasks(patient_id=pid, include_done=False))
        if open_cnt > 0:
            rows.append({"patient": f"{name} — {pid}", "open_tasks": open_cnt})

    with card("Patients needing attention (most open tasks)"):
        if not rows:
            st.caption("No patients with open tasks. 🎉")
            return

        df = pd.DataFrame(rows).sort_values("open_tasks", ascending=False).head(top_n).reset_index(drop=True)
        max_open = int(df["open_tasks"].max()) or 1  # scale for progress bar

        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "patient": st.column_config.TextColumn(
                    "Patient",
                    help="Name — ID",
                    width="medium",
                ),
                "open_tasks": st.column_config.ProgressColumn(
                    "Open tasks",
                    help="Higher means more attention needed",
                    min_value=0,
                    max_value=max_open,
                    format="%d",
                ),
            },
        )

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")
apply_theme()
set_altair_dark_theme()
svc = MedicalStaffService()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def df(items: List[Dict[str, Any]], fields: List[str]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=fields)
    out = [{k: it.get(k) for k in fields} for it in items]
    df_ = pd.DataFrame(out)
    for col in ("timestamp", "when", "uploaded_at", "created_at", "dt"):
        if col in df_.columns:
            with pd.option_context("mode.chained_assignment", None):
                try:
                    df_[col] = pd.to_datetime(df_[col])
                except Exception:
                    pass
    return df_

def all_patients(assigned_to: str | None):
    return svc.search_patients("", assigned_to=assigned_to)

# ---------------------------------------------------------------------------
# Sidebar context
# ---------------------------------------------------------------------------
with st.sidebar:
    st.caption("Context")
    staff_id = st.text_input(
        "Staff ID (for audit)",
        value=st.session_state.get("auth_user", "S001"),
        key="dash_staff_id",
    )
    only_mine = st.toggle("Only my patients", value=False, key="dash_onlymine")

patients = all_patients(staff_id if only_mine else None)
scope_opts = ["All patients"] + [f"{p.get('name','(no name)')} — {p.get('id','')}" for p in patients]
scope_sel = st.selectbox("Scope", scope_opts, index=0)
sel_pid = None
sel_patient = None
if scope_sel != "All patients":
    i = scope_opts.index(scope_sel) - 1
    sel_patient = patients[i]
    sel_pid = sel_patient["id"]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
title = "Dashboard"
subtitle = (
    f"Welcome, {staff_id or '—'}. "
    + ("Overview across **all patients**." if sel_pid is None else f"Focused on **{sel_patient.get('name','(no name)')}** ({sel_pid}).")
)
page_header(title, subtitle, "🏠")

# Subtitle pills
st.markdown(
    """
<style>
.cl-pillbar {display:flex; gap:.5rem; flex-wrap:wrap; margin:-6px 0 12px 4px;}
.cl-pill {
  padding:.25rem .6rem; border-radius:999px;
  border:1px solid rgba(255,255,255,.16);
  background:rgba(255,255,255,.05);
  font-size:.85rem; color:#EAF2FF;
}
</style>
""",
    unsafe_allow_html=True,
)
pill_scope = "Scope: All patients" if sel_pid is None else f"Scope: {sel_patient.get('name')}"
pill_staff = f"Staff: {staff_id or '—'}"
pill_mode = "My patients only" if only_mine else "All assigned"
st.markdown(
    f"""
<div class="cl-pillbar">
  <div class="cl-pill">🧭 {pill_scope}</div>
  <div class="cl-pill">🩺 {pill_staff}</div>
  <div class="cl-pill">📌 {pill_mode}</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data windows
# ---------------------------------------------------------------------------
now = datetime.now()
week_back = now - timedelta(days=7)
week_ahead = now + timedelta(days=7)

def iterate_scope(fn):
    """Apply a service function across scope and merge results."""
    if sel_pid:
        return fn(sel_pid)
    out = []
    for p in patients:
        out += fn(p["id"])
    return out

appts_7d = svc.list_appointments(for_patient=sel_pid, to_iso=week_ahead.isoformat(timespec="minutes"))
open_tasks_list = iterate_scope(lambda pid: svc.list_tasks(pid, include_done=False))
meds_week = [m for m in iterate_scope(lambda pid: svc.list_med_admin(pid, days=7, limit=1000)) if m.get("given")]
msgs_week = []
for p in ([sel_patient] if sel_patient else patients):
    msgs = svc.list_messages_for_patient(p["id"], limit=500)
    msgs_week += [m for m in msgs if m.get("from_role") == "staff" and pd.to_datetime(m.get("timestamp", now)) >= week_back]

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
.kpi-grid {display:grid; grid-template-columns: repeat(4, 1fr); gap:14px; margin:6px 0 18px;}
.kpi {
  background: linear-gradient(180deg, rgba(124,180,255,.12), rgba(255,255,255,.04));
  border:1px solid rgba(255,255,255,.18);
  border-radius:14px; padding:14px 16px;
  box-shadow: 0 8px 24px rgba(0,0,0,.45);
}
.kpi .kpi-label {font-size:.9rem; color:#D7E1F9; margin-bottom:4px;}
.kpi .kpi-value {font-size:2.0rem; font-weight:900; letter-spacing:.5px; color:#F9FBFF;}
.kpi .kpi-emoji {font-size:1.2rem; margin-right:.35rem}
</style>
""",
    unsafe_allow_html=True,
)

kpi_html = f"""
<div class="kpi-grid">
  <div class="kpi"><div class="kpi-label"><span class="kpi-emoji">📅</span>Upcoming appts (7d)</div><div class="kpi-value">{len(appts_7d)}</div></div>
  <div class="kpi"><div class="kpi-label"><span class="kpi-emoji">✅</span>Open tasks</div><div class="kpi-value">{len(open_tasks_list)}</div></div>
  <div class="kpi"><div class="kpi-label"><span class="kpi-emoji">💊</span>Meds given (7d)</div><div class="kpi-value">{len(meds_week)}</div></div>
  <div class="kpi"><div class="kpi-label"><span class="kpi-emoji">💬</span>Msgs sent (7d)</div><div class="kpi-value">{len(msgs_week)}</div></div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Charts row
# ---------------------------------------------------------------------------
lc, rc = st.columns(2)

with lc, card("Appointments next 7 days"):
    if not appts_7d:
        st.caption("No upcoming appointments.")
    else:
        # bucket by date for the next 7 days
        days = [(now + timedelta(days=i)).date() for i in range(0, 7)]
        base = pd.DataFrame({"day": pd.to_datetime(days)})

        # FIX: use 'when' (ISO) from service
        a_df = df(appts_7d, ["when", "patient_id"])
        a_df["day"] = pd.to_datetime(a_df["when"]).dt.date
        grp = a_df.groupby("day").size().reset_index(name="count")
        grp["day"] = pd.to_datetime(grp["day"])
        merged = base.merge(grp, on="day", how="left").fillna(0)

        chart = alt.Chart(merged).mark_area(point=True, interpolate="monotone").encode(
            x=alt.X("day:T", title="Day"),
            y=alt.Y("count:Q", title="Appointments"),
            tooltip=[alt.Tooltip("day:T", title="Day"), alt.Tooltip("count:Q", title="Count")],
        ).properties(height=220)
        st.altair_chart(chart, use_container_width=True)

with rc, card("Med administrations per day (7 days)"):
    meds = [pd.to_datetime(m.get("timestamp", now)).date() for m in meds_week]
    if not meds:
        st.caption("No administrations recorded this week.")
    else:
        base_days = [(now - timedelta(days=i)).date() for i in range(6, -1, -1)]
        base = pd.DataFrame({"day": pd.to_datetime(base_days)})
        m_df = pd.DataFrame({"day": pd.to_datetime(meds)})
        counts = m_df.groupby("day").size().reset_index(name="given")
        merged = base.merge(counts, on="day", how="left").fillna(0)
        chart = alt.Chart(merged).mark_bar().encode(
            x=alt.X("day:T", title="Day"),
            y=alt.Y("given:Q", title="Meds given"),
            tooltip=[alt.Tooltip("day:T", title="Day"), alt.Tooltip("given:Q", title="Given")],
        ).properties(height=220)
        st.altair_chart(chart, use_container_width=True)

# ---------------------------------------------------------------------------
# Attention & documents row
# ---------------------------------------------------------------------------
c1, c2 = st.columns([1.2, 1])

# Beautiful table version (progress bar) — as requested
with c1:
    render_attention_table(svc, staff_id=staff_id, only_my=only_mine, top_n=10)

with c2, card("Recent documents"):
    scope = ([sel_patient] if sel_patient else patients)
    docs: List[Dict[str, Any]] = []
    for p in scope:
        pid = p.get("id")
        for d in svc.list_documents(pid, limit=50):
            docs.append(
                {
                    "when": d.get("uploaded_at", ""),
                    "patient": f"{p.get('name','(no name)')} — {pid}",
                    "name": d.get("name", ""),
                    "kind": (d.get("kind") or "").title() or "Document",
                    "note": d.get("note", ""),
                }
            )
    docs = sorted(docs, key=lambda x: x.get("when", ""), reverse=True)[:8]
    if not docs:
        st.caption("No recent document uploads.")
    else:
        df_docs = pd.DataFrame(docs)
        st.dataframe(
            df_docs,
            hide_index=True,
            use_container_width=True,
            column_config={
                "when": st.column_config.DatetimeColumn("When", format="YYYY-MM-DD HH:mm:ss"),
                "patient": st.column_config.TextColumn("Patient"),
                "name": st.column_config.TextColumn("File name"),
                "kind": st.column_config.TextColumn("Type"),
                "note": st.column_config.TextColumn("Note"),
            },
        )

# ---------------------------------------------------------------------------
# Quick actions
# ---------------------------------------------------------------------------
PAGES_DIR = Path(__file__).resolve().parent  # .../medical_staff/pages

def link_for(token: str, *, label: str, icon: str):
    """Find first page in the pages/ folder whose filename contains `token`."""
    for p in sorted(PAGES_DIR.glob("*.py")):
        if token.lower() in p.name.lower():
            st.page_link(f"pages/{p.name}", label=label, icon=icon)
            return
    st.write(f"⚠️ Missing page for “{token}”")

with card("Quick actions"):
    a, b, c, d = st.columns(4)
    with a: link_for("Vitals", label="Open Vitals tool", icon="🩺")
    with b: link_for("MAR", label="Administer medication", icon="💊")
    with c: link_for("Observations", label="Log observation", icon="📝")
    with d: link_for("Tasks", label="View tasks", icon="✅")

    a2, b2, c2, d2 = st.columns(4)
    with a2: link_for("Appointments", label="Manage appointments", icon="📅")
    with b2: link_for("Messages", label="Send message", icon="💬")
    with c2: link_for("Documents", label="Upload documents", icon="📄")
    with d2: link_for("Audit", label="Audit trail", icon="🧾")

# ---------------------------------------------------------------------------
# Activity feed
# ---------------------------------------------------------------------------
with card("Recent activity"):
    scope = ([sel_patient] if sel_patient else patients)
    aud = []
    for p in scope:
        aud += svc.list_audit(who=None, patient_id=p["id"], limit=10)
    if not aud:
        st.caption("No recent activity.")
    else:
        try:
            aud = sorted(aud, key=lambda x: x.get("when", ""), reverse=True)[:10]
        except Exception:
            aud = aud[:10]
        for a in aud:
            st.write(
                f"• **{a.get('when','')}** — {a.get('who','')} — **{a.get('action','')}** — "
                f"{a.get('target','')} — {a.get('detail','')}"
            )
