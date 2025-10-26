# carelog_nurse/pages/5_✅_Tasks.py
from __future__ import annotations
from datetime import datetime, timedelta, date, time
import streamlit as st

from components.ui import apply_theme, page_header
from app.nurse_service import NurseService
from app.data_adapter import DataAdapter  # <-- NEW

# ---------- helpers ----------
def _safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except Exception:
            pass

def _combine(d: date, t: time) -> datetime:
    return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second)

def _parse_iso(s: str | None) -> datetime | None:
    if not s: return None
    try:
        # allow trailing Z
        return datetime.fromisoformat(s.replace("Z",""))
    except Exception:
        return None

# ---------- page ----------
st.set_page_config(page_title="Tasks", page_icon="✅", layout="wide")
apply_theme()

# Extra dark UI + **global white fonts** + chips (UNCHANGED)
st.markdown("""
<style>
  :root{
    --bg:#0f1a2b; --ink:#ffffff; --sub:#e5eeff; --edge:#1e3350; --card:#0e1726;
    --input:#132236; --inputEdge:#274264;
  }
  html, body, div, span, p, li, strong, em, small, h1, h2, h3, h4, h5, h6 { color:var(--ink) !important; }
  label, .stMarkdown, [data-testid="stMarkdownContainer"] * { color:var(--ink) !important; }
  ::placeholder { color:#e0ecff !important; opacity:1; }
  .panel { background:var(--bg); border:1px solid var(--edge); border-radius:18px; padding:16px; }
  .panel h3 { margin:0 0 10px 0; font-size:16px; font-weight:900; color:var(--ink); }
  input, textarea, select {
    background:var(--input) !important; color:var(--ink) !important;
    border:1px solid var(--inputEdge) !important; border-radius:10px !important;
  }
  [data-baseweb="select"]>div,
  [data-testid="stDateInput"] input,
  [data-testid="stTimeInput"] input,
  [data-testid="stTextArea"] textarea,
  [data-testid="stTextInput"] input,
  [data-testid="stNumberInput"] input {
    background:var(--input) !important; color:var(--ink) !important; border:1px solid var(--inputEdge) !important;
  }
  .stApp [data-baseweb="popover"] [data-baseweb="menu"],
  .stApp div[role="listbox"]{
    background:#0f1a2b !important; color:var(--ink) !important;
    border:1px solid var(--inputEdge) !important; border-radius:10px !important;
  }
  .stApp [data-baseweb="popover"] [role="option"],
  .stApp div[role="option"]{
    color:var(--ink) !important; background:transparent !important;
  }
  .stApp [data-baseweb="popover"] [role="option"]:hover,
  .stApp div[role="option"]:hover{
    background:#132a48 !important; color:var(--ink) !important;
  }
  .stApp [data-baseweb="popover"] [role="option"][aria-selected="true"],
  .stApp div[role="option"][aria-selected="true"]{
    background:#17365f !important; color:var(--ink) !important;
  }
  .stButton>button {
    border:1px solid #5b8bda; background:#2a4f8a; color:#ffffff;
    padding:8px 14px; border-radius:10px; font-weight:800;
    box-shadow:0 6px 16px rgba(0,0,0,.35);
  }
  .stButton>button:hover { background:#3564b3; border-color:#7fb0ff; }
  .tcard{ background:var(--card); border:1px solid #213651; border-radius:14px; padding:12px; margin-bottom:10px; }
  .trow{ display:flex; gap:12px; align-items:center; justify-content:space-between; }
  .tleft{ display:flex; flex-direction:column; gap:6px; }
  .title{ font-weight:900; color:var(--ink); }
  .meta{ color:var(--sub); font-size:12px; }
  .chips{ display:flex; gap:6px; flex-wrap:wrap; }
  .pill{ display:inline-block; padding:3px 10px; border-radius:999px; font-weight:800; font-size:11px; }
  .prio-high{ background:#ff6b6b; color:#0b1320; }
  .prio-medium{ background:#ffd166; color:#0b1320; }
  .prio-low{ background:#27d6c3; color:#0b1320; }
  .state-overdue{ background:#c62828; color:#fff; }
  .state-soon{ background:#ff8f00; color:#0b1320; }
  .state-scheduled{ background:#1e88e5; color:#0b1320; }
  .state-done{ background:#2bb673; color:#0b1320; }
  .section-title{ font-weight:900; font-size:18px; color:var(--ink); margin:14px 0 8px 0; }
</style>
""", unsafe_allow_html=True)

page_header("Daily Tasks", "Prioritized list with due times & completion", "✅")

svc = NurseService()

# ---------- Patients from data/patients.json (linked like Patients page) ----------
adapter = DataAdapter()
p_src = adapter.patients()
if not p_src and hasattr(svc, "list_patients"):
    p_src = svc.list_patients()

# Normalize to list[dict]
if isinstance(p_src, dict):
    patients = [p_src[k] for k in sorted(p_src.keys()) if isinstance(p_src[k], dict)]
elif isinstance(p_src, list):
    patients = [p for p in p_src if isinstance(p, dict)]
else:
    patients = []

# Build id -> name map
id_to_name: dict[str, str] = {}
for p in patients:
    pid = p.get("id") or p.get("patient_id")
    if not pid:
        continue
    id_to_name[pid] = p.get("name") or p.get("full_name") or p.get("Name") or pid

# ===== Add Task =====
st.markdown('<div class="panel"><h3>Add Task</h3>', unsafe_allow_html=True)

c1, c2 = st.columns([2, 2])
with c1:
    title = st.text_input("Title", placeholder="e.g., Morning vitals for p001")
with c2:
    now_plus = datetime.utcnow() + timedelta(hours=1)
    dd = st.date_input("Due date", value=now_plus.date())
    tt = st.time_input("Due time", value=now_plus.time().replace(second=0, microsecond=0))

priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)

focus_pid = st.session_state.get("patient_focus")
pid_options = [""] + [pid for pid in id_to_name.keys()]
default_index = pid_options.index(focus_pid) if (focus_pid and focus_pid in pid_options) else 0
pid = st.selectbox(
    "Link to patient (optional)",
    pid_options, index=default_index,
    format_func=lambda i: "—" if i=="" else id_to_name.get(i, i)
)

col_add, _ = st.columns([1, 5])
if col_add.button("Create Task"):
    due_dt = _combine(dd, tt).replace(microsecond=0)
    if not title.strip():
        st.warning("Please enter a title.")
    else:
        svc.add_task(title.strip(), due_dt.isoformat(), priority, pid or None)
        st.success("Task added.")
        _safe_rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ===== Task Lists (beautiful cards) =====
tasks = svc.list_tasks()
st.markdown('<div class="panel"><h3>My Tasks</h3>', unsafe_allow_html=True)

if not tasks:
    st.info("No tasks yet.")
else:
    # categorize
    now = datetime.utcnow()
    overdue, today, upcoming, done = [], [], [], []
    for t in tasks:
        status = (t.get("status") or "").lower()
        due = _parse_iso(t.get("due_at"))
        prio = (t.get("priority") or "low").lower()
        if status in {"done","completed","complete"}:
            done.append((t, due, prio))
        else:
            if due:
                if due.date() < now.date() or (due.date()==now.date() and due < now):
                    overdue.append((t, due, prio))
                elif due.date() == now.date():
                    today.append((t, due, prio))
                else:
                    upcoming.append((t, due, prio))
            else:
                upcoming.append((t, due, prio))

    def _prio_chip(p:str)->str:
        return f"<span class='pill prio-{p}'>priority: {p}</span>"

    def _state_chip(kind:str)->str:
        cls = {"overdue":"state-overdue","soon":"state-soon","scheduled":"state-scheduled","done":"state-done"}[kind]
        label = {"overdue":"overdue","soon":"due today","scheduled":"scheduled","done":"completed"}[kind]
        return f"<span class='pill {cls}'>{label}</span>"

    def _patient_name(pid:str|None)->str:
        if not pid: return "—"
        return id_to_name.get(pid, pid)

    def _render_group(title:str, items:list[tuple[dict,datetime,str]], state_key:str):
        if not items:
            return
        st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
        for t, due, prio in sorted(items, key=lambda x: x[1] or datetime.max):
            tid = t.get("id")
            ttitle = t.get("title","")
            patient = _patient_name(t.get("patient_id"))
            due_txt = due.strftime("%Y-%m-%d %H:%M") if due else "—"
            kind = "done" if state_key=="done" else ("overdue" if state_key=="overdue" else ("soon" if state_key=="today" else "scheduled"))
            chips = f"{_prio_chip(prio)} {_state_chip(kind)}"
            st.markdown(
                f"""
                <div class='tcard'>
                  <div class='trow'>
                    <div class='tleft'>
                      <div class='title'>{ttitle}</div>
                      <div class='meta'>Due: <b>{due_txt}</b> · Patient: <b>{patient}</b> · ID: {tid}</div>
                      <div class='chips'>{chips}</div>
                    </div>
                    <div>
                """, unsafe_allow_html=True
            )
            c1, c2 = st.columns([1,1])
            with c1:
                if state_key!="done":
                    if st.button("Complete", key=f"done_{tid}"):
                        svc.complete_task(tid)
                        st.success("Task completed.")
                        _safe_rerun()
            with c2:
                if state_key!="done" and due:
                    if st.button("Snooze +30m", key=f"snooze_{tid}"):
                        new_due = (due + timedelta(minutes=30)).replace(microsecond=0).isoformat()
                        try:
                            if hasattr(svc, "reschedule_task"):
                                svc.reschedule_task(tid, new_due)
                            else:
                                svc.complete_task(tid)
                                svc.add_task(ttitle, new_due, prio, t.get("patient_id"))
                            st.success("Snoozed 30 minutes.")
                        except Exception:
                            st.warning("Snooze not supported by service.")
                        _safe_rerun()
            st.markdown("</div></div>", unsafe_allow_html=True)

    _render_group("Overdue", overdue, "overdue")
    _render_group("Today", today, "today")
    _render_group("Upcoming", upcoming, "upcoming")
    _render_group("Completed", done, "done")

st.markdown('</div>', unsafe_allow_html=True)
