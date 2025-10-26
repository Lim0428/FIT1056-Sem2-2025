# carelog_nurse/pages/4_🗓️_Appointments.py
from __future__ import annotations
import calendar
from datetime import datetime, timedelta, date, time
import streamlit as st

from components.ui import apply_theme, page_header
from app.nurse_service import NurseService

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

def _parse_iso(dt_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None

def _month_bounds(d: date) -> tuple[date, date]:
    first = d.replace(day=1)
    last_day = calendar.monthrange(first.year, first.month)[1]
    last = d.replace(day=last_day)
    return first, last

def _times_30min(start: time = time(8, 0), end: time = time(18, 0)):
    out = []
    cur = datetime(2000, 1, 1, start.hour, start.minute)
    stop = datetime(2000, 1, 1, end.hour, end.minute)
    while cur <= stop:
        out.append(cur.time().replace(second=0, microsecond=0))
        cur += timedelta(minutes=30)
    return out

# ---------- page ----------
st.set_page_config(page_title="Appointments", page_icon="🗓️", layout="wide")
apply_theme()

# Dark styling + **global white fonts** + calendar look
st.markdown("""
<style>
  :root{
    --bg:#0f1a2b; --ink:#ffffff; --edge:#1e3350; --input:#132236; --inputEdge:#274264;
    --muted:#e5eeff; --card:#0e1726;
  }

  /* GLOBAL: force all text white for clarity on dark surfaces */
  html, body, div, span, p, li, strong, em, small, h1, h2, h3, h4, h5, h6 { color:var(--ink) !important; }
  label, .stMarkdown, [data-testid="stMarkdownContainer"] * { color:var(--ink) !important; }
  ::placeholder { color:#e0ecff !important; opacity:1; }

  /* Panels & buttons */
  .panel { background:var(--bg); border:1px solid var(--edge); border-radius:18px; padding:16px; }
  .panel h3 { margin:0 0 10px 0; font-size:16px; font-weight:900; color:var(--ink); }
  .stButton>button {
    border:1px solid #5b8bda; background:#2a4f8a; color:#ffffff;
    padding:8px 12px; border-radius:10px; font-weight:800;
  }
  .stButton>button:hover { background:#3564b3; border-color:#7fb0ff; }
  .muted{ color:var(--muted); }

  /* Inputs: dark shells + white text */
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
  /* Dropdown menu portal (BaseWeb) -> dark with white option text */
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

  /* Calendar visuals */
  .cal-wrap{ background:var(--bg); border:1px solid var(--edge); border-radius:18px; padding:12px 12px; }
  .cal-header{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
  .cal-title{ font-weight:900; font-size:16px; color:var(--ink); }
  .dow{ color:#d9e6ff; font-weight:800; text-transform:uppercase; letter-spacing:.05em; font-size:12px; }
  .cell{ background:#0e1726; border:1px solid #213651; border-radius:12px; padding:8px; height:84px; position:relative; }
  .cell.today{ outline:2px solid #2e7ef7; }
  .cell .num{ font-weight:900; color:#eaf2ff; }
  .cell .count{ position:absolute; right:8px; bottom:8px; background:#17263a; color:#d7e6fb; font-size:11px; padding:2px 6px; border-radius:999px; }

  /* Upcoming table (beauty) */
  .title-card{ background:#0d1a2d; border:1px solid var(--edge); border-radius:18px; padding:14px; font-weight:900; }
  .tbl-wrap{ margin-top:8px; }
  table.beauty{ width:100%; border-collapse:separate; border-spacing:0;
                background:linear-gradient(180deg,#0d1b2b,#0a1524); color:#ffffff;
                border:1px solid var(--edge); border-radius:16px; overflow:hidden; }
  .beauty thead th{
    background:#0e2036; color:#d9e6ff; font-weight:900; font-size:13px; letter-spacing:.06em;
    text-transform:uppercase; padding:14px 12px; border-bottom:1px solid var(--edge);
  }
  .beauty tbody td{ padding:14px 12px; border-bottom:1px solid rgba(255,255,255,.05); }
  .beauty tbody tr:nth-child(even){ background:#0b1a31; }
  .beauty tbody tr:hover{ background:#0e2a4f; }
  .pill{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:800; }
  .p-booked{ background:#1a2f4d; color:#9bd1ff; border:1px solid #3f6fb5; }
  .p-cancelled{ background:#3a1a1a; color:#ffb3b3; border:1px solid #a74c4c; }
  .p-done{ background:#12331f; color:#a1f2c8; border:1px solid #2b8758; }
  .note-muted{ color:#cfe0ff; }
</style>
""", unsafe_allow_html=True)

page_header("Appointments", "View / book / reschedule (30-min slots; no past time)", "🗓️")

svc = NurseService()
patients = svc.list_patients()

# ---- state sync BEFORE widget creation (important) ----
if "appt_date" in st.session_state:
    if st.session_state.get("start_date") != st.session_state["appt_date"]:
        # Safe: set widget state value before the widget is instantiated
        st.session_state["start_date"] = st.session_state["appt_date"]

# Default patient focus
focus_pid = st.session_state.get("patient_focus")
pid_options = [p["id"] for p in patients]
default_idx = pid_options.index(focus_pid) if focus_pid in pid_options else 0

# -------- Booking form --------
st.markdown('<div class="panel"><h3>Book new appointment</h3>', unsafe_allow_html=True)
pid = st.selectbox(
    "Patient",
    options=pid_options,
    index=default_idx,
    format_func=lambda i: next(p["name"] for p in patients if p["id"] == i),
)
clinician_id = st.text_input("Clinician ID", value="dr_001")

c1, c2, c3 = st.columns([1.2, 1, 1])
with c1:
    # Use the synced session state default
    sel_date_default = st.session_state.get("start_date", date.today())
    sel_date = st.date_input("Start date", value=sel_date_default, key="start_date")
with c2:
    t_choices = _times_30min()
    now = datetime.utcnow() + timedelta(minutes=30)
    nearest = min(t_choices, key=lambda tt: abs((datetime.combine(date.today(), tt) - now).total_seconds()))
    sel_time = st.selectbox("Start time", options=t_choices, index=t_choices.index(nearest), format_func=lambda t: t.strftime("%H:%M"))
with c3:
    dur = st.selectbox("Duration", options=[30, 60, 90], index=0, format_func=lambda m: f"{m} minutes")

if st.button("Book Appointment"):
    start_dt = _combine(st.session_state.get("start_date", date.today()), sel_time)
    try:
        svc.book_appointment(pid, clinician_id, start_dt)
        st.success("Appointment booked.")
        _safe_rerun()
    except Exception as e:
        st.error(str(e))
st.markdown('</div>', unsafe_allow_html=True)

# -------- Calendar + agenda --------
left, right = st.columns([1.1, 1])

# === Left: Month calendar (clickable days) ===
with left:
    cal_date = st.session_state.get("cal_date", st.session_state.get("start_date", date.today()))
    first, last = _month_bounds(cal_date)
    appts_all = svc.list_appointments()

    # date -> count
    counts: dict[date, int] = {}
    for a in appts_all:
        st_dt = _parse_iso(a.get("start", "")) or _parse_iso(a.get("time", ""))
        if not st_dt:
            continue
        k = st_dt.date()
        counts[k] = counts.get(k, 0) + 1

    st.markdown('<div class="cal-wrap">', unsafe_allow_html=True)
    h1, h2, h3 = st.columns([1, 2, 1])
    with h1:
        if st.button("← Prev"):
            prev_m = (first.replace(day=1) - timedelta(days=1)).replace(day=1)
            st.session_state["cal_date"] = prev_m
            _safe_rerun()
    with h2:
        st.markdown(f'<div class="cal-header"><div class="cal-title">{first.strftime("%B %Y")}</div></div>', unsafe_allow_html=True)
    with h3:
        if st.button("Next →"):
            next_month = (last + timedelta(days=1)).replace(day=1)
            st.session_state["cal_date"] = next_month
            _safe_rerun()

    # weekday header
    cols = st.columns(7)
    for idx, wd in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
        cols[idx].markdown(f"<div class='dow'>{wd}</div>", unsafe_allow_html=True)

    # calendar grid
    month = calendar.Calendar(firstweekday=0)
    weeks = month.monthdatescalendar(first.year, first.month)
    today_d = date.today()

    for wk in weeks:
        cols = st.columns(7)
        for i, d in enumerate(wk):
            is_cur_month = (d.month == first.month)
            style = "cell today" if d == today_d else "cell"
            num_color = "#eaf2ff" if is_cur_month else "#6f86a5"
            cnt = counts.get(d, 0)
            count_html = f"<div class='count'>{cnt} appt</div>" if cnt else ""
            with cols[i]:
                cell_html = (
                    f"<div class='{style}'>"
                    f"<div class='num' style='color:{num_color}'>{d.day}</div>"
                    f"{count_html}"
                    f"</div>"
                )
                st.markdown(cell_html, unsafe_allow_html=True)
                if st.button("Select", key=f"sel_{d.isoformat()}"):
                    # Do not write to widget key directly; set appt_date & rerun
                    st.session_state["appt_date"] = d
                    st.session_state["cal_date"] = d
                    _safe_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# === Right: Agenda for selected date + modify ===
with right:
    st.markdown('<div class="panel"><h3>Agenda</h3>', unsafe_allow_html=True)
    sel_day = st.session_state.get("appt_date", st.session_state.get("start_date", date.today()))

    appts_for_patient = svc.list_appointments(patient_id=pid)
    day_items = []
    for a in appts_for_patient:
        st_dt = _parse_iso(a.get("start", "")) or _parse_iso(a.get("time", ""))
        if st_dt and st_dt.date() == sel_day:
            day_items.append(a)

    st.caption(f"Selected date: {sel_day.isoformat()}")
    if not day_items:
        st.info("No appointments for this patient on this day.")
    else:
        for a in sorted(day_items, key=lambda x: x.get("start","")):
            st_time = _parse_iso(a.get("start",""))
            time_txt = st_time.strftime('%H:%M') if st_time else ''
            st.markdown(f"**{time_txt}** · {a.get('clinician_id','')} · {a.get('status','')}")
            r1, r2, r3 = st.columns([1,1,2])
            with r1:
                slot = st.selectbox(
                    f"New time for {a['id']}",
                    options=_times_30min(),
                    key=f"slot_{a['id']}",
                    format_func=lambda t: t.strftime("%H:%M")
                )
            with r2:
                if st.button("Reschedule", key=f"res_{a['id']}"):
                    try:
                        svc.reschedule_appointment(a["id"], _combine(sel_day, slot))
                        st.success("Rescheduled.")
                        _safe_rerun()
                    except Exception as e:
                        st.error(str(e))
            with r3:
                if st.button("Cancel", key=f"cancel_{a['id']}"):
                    svc.cancel_appointment(a["id"])
                    st.warning("Cancelled.")
                    _safe_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -------- Upcoming table (patient) --------
st.markdown("")
st.markdown("<div class='title-card'>Upcoming</div>", unsafe_allow_html=True)
appts = svc.list_appointments(patient_id=pid)

def _fmt(dt_str: str) -> str:
    d = _parse_iso(dt_str)
    return d.strftime("%Y-%m-%d %H:%M") if d else (dt_str or "")

def _pill(status: str) -> str:
    s = (status or "").lower()
    cls = "p-booked"
    if "cancel" in s:
        cls = "p-cancelled"
    elif "done" in s or "complete" in s:
        cls = "p-done"
    return f"<span class='pill {cls}'>{status or ''}</span>"

if appts:
    rows_html = []
    for a in appts:
        rows_html.append(
            "<tr>"
            f"<td>{a.get('id','')}</td>"
            f"<td>{_fmt(a.get('start','') or a.get('time',''))}</td>"
            f"<td>{_fmt(a.get('end',''))}</td>"
            f"<td>{a.get('clinician_id','')}</td>"
            f"<td>{_pill(a.get('status',''))}</td>"
            f"<td class='note-muted'>{a.get('note','')}</td>"
            "</tr>"
        )

    html = (
        "<div class='tbl-wrap'>"
        "<table class='beauty'>"
        "<thead><tr>"
        "<th>ID</th><th>Start</th><th>End</th><th>Clinician</th><th>Status</th><th>Note</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "</table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)
else:
    st.info("No appointments for this patient yet.")
