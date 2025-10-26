# carelog_nurse/pages/0_🏠_Dashboard.py
from __future__ import annotations
import json
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
from calendar import monthrange

from components.ui import apply_theme, page_header, kpi_row_colored
from app.data_adapter import DataAdapter

# ---------- Page + theme ----------
st.set_page_config(page_title="🏠 Overview", page_icon="🏠", layout="wide")
apply_theme()
page_header("Overview", "Today at a glance", "🏠")

# ---------- Small CSS helpers ----------
st.markdown("""
<style>
  .panel { background:#0f1a2b; border:1px solid #1e3350; border-radius:18px; padding:16px; }
  .panel h3 { margin:0 0 10px 0; font-size:16px; font-weight:900; color:#eaf2ff; }

  .mini-row { display:flex; align-items:center; justify-content:space-between;
              background:#0e1726; border:1px solid #213651; border-radius:12px;
              padding:8px 10px; margin-bottom:8px; }
  .mini-left { display:flex; align-items:center; gap:10px; color:#eaf2ff; }
  .mini-row .time { color:#9fb0c3; font-size:13px; min-width:64px; text-align:right; }
  .avatar { width:26px; height:26px; border-radius:999px; background:#22324a; display:inline-block; }
  .muted { color:#a9bed6; }

  /* --- Appointments card list --- */
  .appt-wrap { display:flex; flex-direction:column; gap:10px; max-height:300px; overflow-y:auto; }
  .appt-card {
    background:#0e1726; border:1px solid #213651; border-radius:14px; padding:12px 14px;
    box-shadow:0 8px 18px rgba(0,0,0,.25);
  }
  .appt-row { display:flex; align-items:center; justify-content:space-between; gap:12px; }
  .appt-left { display:flex; align-items:center; gap:12px; }
  .appt-avatar { width:34px; height:34px; border-radius:999px; background:#22324a; }
  .appt-name { color:#eaf2ff; font-weight:800; }
  .appt-sub  { color:#9fb0c3; font-size:12px; }

  .chip { display:inline-block; padding:6px 10px; border-radius:999px; font-weight:800; font-size:11px; }
  .chip-type { background:#17365f; color:#cfe5ff; border:1px solid #274b7f; }

  .date-badge {
    background:#112133; color:#cfe5ff; border:1px solid #203a5a;
    padding:6px 12px; border-radius:10px; font-weight:800; font-size:13px;
  }
  .appt-wrap::-webkit-scrollbar { width:8px; }
  .appt-wrap::-webkit-scrollbar-thumb { background:#2a3d5c; border-radius:8px; }

  /* Make the time *button* look like the old chip, but clickable */
  .appt-time .stButton > button {
    border:1px solid #2a405c; background:#1b2a3c; color:#eaf2ff;
    padding:6px 12px; border-radius:999px; font-weight:800; font-size:11px;
  }
  .appt-time .stButton > button:hover { background:#22364f; border-color:#385779; }
</style>
""", unsafe_allow_html=True)

# ---------- Data ----------
data = DataAdapter()
k = data.counts_for_kpis()
doctors = data.doctors()
doctors_count = len(doctors) if isinstance(doctors, list) else 0

# ---------- KPI row ----------
kpi_row_colored([
    {"label":"Doctor",  "value": doctors_count,      "hint":"Last 7 days",    "class":"doctor"},
    {"label":"Patient", "value": k["patients"],      "hint":"Last 7 days",    "class":"patient"},
    {"label":"Surgery", "value": 0,                  "hint":"(sample tile)",  "class":"surgery"},
    {"label":"Report",  "value": k["unread_alerts"], "hint":"Unread alerts",  "class":"report"},
])

st.markdown("")

# ---------- Helpers (appointments + lists) ----------
def _load_json_file(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
            return obj if obj is not None else default
    except Exception:
        return default

def _today_iso() -> str:
    return date.today().isoformat()

def _parse_dt_any(x) -> datetime | None:
    if not x: return None
    s = str(x).strip().replace("/", "-")
    try:
        if "T" in s:
            return datetime.fromisoformat(s)
        return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
    except Exception:
        return None

def _safe_name(p: dict) -> str:
    return p.get("name") or p.get("full_name") or p.get("Name") or p.get("id") or p.get("patient_id") or "Patient"

def _collect_today_appts_cards() -> list[dict]:
    """
    Returns list of dicts for *today* from either schema:
    1) Flat: [{patient_id, start|time|dt, type}, ...]
    2) Nested per patient:
       [{id,name,appointments:[{dt, note, id},...]}, ...]
    Each row includes: name, gender, time, type, pid.
    """
    today = _today_iso()
    pts_list = [p for p in data.patients() if isinstance(p, dict)]
    pts_by_id = {p.get("id") or p.get("patient_id"): p for p in pts_list}

    out: list[dict] = []

    # ---- Flat style (via adapter.appointments) ----
    for a in data.appointments():
        if not isinstance(a, dict): 
            continue
        ts = a.get("start") or a.get("time") or a.get("dt") or a.get("datetime") or a.get("date") or a.get("ts")
        if not ts:
            continue
        dtv = _parse_dt_any(ts)
        if not dtv or dtv.date().isoformat() != today:
            continue
        pid = a.get("patient_id") or a.get("pid") or a.get("id")
        p = pts_by_id.get(pid, {})
        out.append({
            "name": _safe_name(p),
            "gender": (p.get("gender") or p.get("sex") or ""),
            "time": dtv.strftime("%H:%M"),
            "type": a.get("type") or a.get("note") or "Consultation",
            "pid": pid or "",
        })

    # ---- Nested per patient style (read file directly) ----
    nested = _load_json_file((data.data_dir / "appointments.json"), [])
    if isinstance(nested, dict):
        nested = [nested]
    for item in nested or []:
        if not isinstance(item, dict): 
            continue
        pid = item.get("id") or item.get("patient_id")
        patient = pts_by_id.get(pid, {"id": pid, "name": item.get("name","")})
        for ap in item.get("appointments", []) or []:
            dtv = _parse_dt_any(ap.get("dt") or ap.get("time") or ap.get("start"))
            if dtv and dtv.date().isoformat() == today:
                out.append({
                    "name": _safe_name(patient),
                    "gender": (patient.get("gender") or patient.get("sex") or ""),
                    "time": dtv.strftime("%H:%M"),
                    "type": ap.get("note") or "Consultation",
                    "pid": pid or "",
                })

    out.sort(key=lambda r: r.get("time",""))
    return out

def _gender_breakdown() -> dict[str, int]:
    out = {"Female": 0, "Male": 0, "Other": 0}
    for p in data.patients():
        g = (p.get("gender") or p.get("sex") or "").strip().lower()
        if g.startswith("f"):
            out["Female"] += 1
        elif g.startswith("m"):
            out["Male"] += 1
        else:
            out["Other"] += 1
    return {k: v for k, v in out.items() if v > 0}

def _safe_name_from_patient(p: dict) -> str:
    return _safe_name(p)

def _goto_vitals(pid: str):
    if pid:
        st.session_state["patient_focus"] = pid
    try:
        st.switch_page("pages/2_🩺_Vitals_&_Notes.py")
    except Exception:
        pass

# ---------- Middle row: line chart (left) + calendar & patient list (right) ----------
left, right = st.columns([2.2, 1])

with left:
    st.markdown('<div class="panel"><h3>Patient visit</h3>', unsafe_allow_html=True)
    series = data.appointments_monthly_series() if hasattr(data, "appointments_monthly_series") else []
    if series:
        df = pd.DataFrame(series, columns=["Month","Count","Type"])
        df["Month"] = pd.to_datetime(df["Month"] + "-01", errors="coerce")
        df = df.dropna(subset=["Month"])
        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X("Month:T", axis=alt.Axis(grid=False, title="")),
                y=alt.Y("Count:Q", axis=alt.Axis(grid=True, title="")),
                color=alt.Color("Type:N", legend=alt.Legend(orient="top-left", direction="horizontal")),
                tooltip=["Month:T","Type:N","Count:Q"]
            )
            .properties(height=280)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No appointment data yet.")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    # ---- Calendar (mini month) ----
    def render_calendar(d: date):
        y, m = d.year, d.month
        first_weekday = date(y, m, 1).weekday()
        days_in_month = monthrange(y, m)[1]
        cells = []
        head = f'<div class="muted" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">{d.strftime("%b %Y")}</div>'
        cells.append('<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px">')
        for wd in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]:
            cells.append(f'<div class="muted" style="font-size:12px;text-align:center">{wd}</div>')
        for _ in range((first_weekday) % 7): cells.append('<div></div>')
        today_iso = date.today().isoformat()
        for day in range(1, days_in_month+1):
            cur = date(y, m, day)
            style = "border:1px solid #1b2a3c;border-radius:10px;padding:6px;text-align:center"
            if cur.isoformat() == today_iso:
                style += ";background:#1b2a3c"
            cells.append(f'<div style="{style}">{day}</div>')
        cells.append('</div>')
        return head + "".join(cells)

    st.markdown('<div class="panel"><h3>Calendar</h3>', unsafe_allow_html=True)
    st.markdown(render_calendar(date.today()), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Patient list (scrolling mini list) ----
    st.markdown('<div class="panel" style="margin-top:12px;"><h3>Patient list</h3>', unsafe_allow_html=True)
    patients = data.patients()
    if patients:
        patients_sorted = sorted(
            (p for p in patients if isinstance(p, dict)),
            key=lambda p: (_safe_name_from_patient(p) or "").lower()
        )
        st.markdown('<div style="max-height:240px; overflow:auto; padding-right:4px;">', unsafe_allow_html=True)
        for p in patients_sorted:
            name = _safe_name_from_patient(p)
            st.markdown(
                f'<div class="mini-row"><div class="mini-left"><span class="avatar"></span>'
                f'<strong>{name}</strong></div><div class="time">—</div></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write("No patients found.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("")

# ---------- Bottom row: Today’s Appointment (cards) + donut ----------
left2, right2 = st.columns([2.2, 1])

with left2:
    st.markdown('<div class="panel"><h3>Today\'s Appointment</h3>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="display:flex; justify-content:flex-end; margin-bottom:8px;"><span class="date-badge">{date.today().strftime("%Y/%m/%d")}</span></div>',
        unsafe_allow_html=True
    )
    appts = _collect_today_appts_cards()
    if not appts:
        st.write("No appointments today.")
    else:
        st.markdown('<div class="appt-wrap">', unsafe_allow_html=True)
        for i, r in enumerate(appts):
            # Card shell
            st.markdown('<div class="appt-card">', unsafe_allow_html=True)
            # Two-column layout inside the card: left text + right time button
            lcol, rcol = st.columns([1, 0.35])
            with lcol:
                st.markdown(
                    f"""
                    <div class="appt-row">
                      <div class="appt-left">
                        <span class="appt-avatar"></span>
                        <div>
                          <div class="appt-name">{r.get('name','')}</div>
                          <div class="appt-sub">{r.get('gender','')}</div>
                        </div>
                      </div>
                      <div class="chip chip-type">{r.get('type','Consultation')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with rcol:
                st.markdown('<div class="appt-time" style="display:flex;justify-content:flex-end;">', unsafe_allow_html=True)
                if st.button(f"🕒 {r.get('time','')}", key=f"appt_time_{i}"):
                    _goto_vitals(r.get("pid",""))
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)  # end card
        st.markdown('</div>', unsafe_allow_html=True)      # end wrap
    st.markdown('</div>', unsafe_allow_html=True)

with right2:
    st.markdown('<div class="panel"><h3>Patients</h3>', unsafe_allow_html=True)
    breakdown = _gender_breakdown()
    if breakdown:
        df = pd.DataFrame({"Category": list(breakdown.keys()), "Value": list(breakdown.values())})
        donut = (
            alt.Chart(df)
            .mark_arc(innerRadius=70)
            .encode(theta="Value:Q", color="Category:N", tooltip=["Category:N","Value:Q"])
            .properties(height=260)
        )
        st.altair_chart(donut, use_container_width=True)
        st.caption(f'Total: {sum(breakdown.values())}')
    else:
        st.write("No patients yet.")
    st.markdown('</div>', unsafe_allow_html=True)
