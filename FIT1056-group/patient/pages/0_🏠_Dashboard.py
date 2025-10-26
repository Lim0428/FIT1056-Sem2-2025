# pages/0_🏠_Dashboard.py
from __future__ import annotations
import streamlit as st
from datetime import datetime, date
import calendar as cal
import pandas as pd
import altair as alt  # colorful trend

from components.ui import apply_theme, card, require_auth
from app.patient import PatientService
from app.auth import AuthService
from app.appointments import AppointmentService
from app.emergency import EmergencyService
from app.storage import read_db
from app.messaging import MessagingService

# ---------- Page setup ----------
st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")
apply_theme()
require_auth()

# ---------- Colorful styling ----------
st.markdown(
    """
    <style>
      :root{
        --bg: #0B1329;
        --bg2:#0A1124;
        --text: #F7FAFF;
        --muted:#E0EAFF;
        --c-blue:#7CB4FF;
        --c-teal:#2DD4BF;
        --c-green:#34D399;
        --c-pink:#EC4899;
        --c-orange:#FB923C;
        --c-purple:#A78BFA;
        --c-yellow:#FDE047;
        --glass: rgba(255,255,255,.08);
        --glass-2: rgba(255,255,255,.12);
      }

      [data-testid="stAppViewContainer"]{ background: var(--bg) !important; color: var(--text) !important; }
      section[data-testid="stSidebar"]{ background: var(--bg2) !important; color: var(--text) !important; }
      section[data-testid="stSidebar"] *{ color: var(--text) !important; }
      [data-testid="stAppViewContainer"] *{ color: var(--text) !important; }
      .muted,.stCaption,.stMetric-label{ color: var(--muted) !important; opacity:.98 !important; }

      .hero{
        position: relative;
        padding: 18px 22px;
        border-radius: 18px;
        background: linear-gradient(135deg,#143061,#0B172E);
        border: 1px solid var(--glass-2);
        box-shadow: 0 25px 60px rgba(0,0,0,.55);
        overflow:hidden;
      }
      .hero:before{
        content:"";
        position:absolute; inset:-2px;
        border-radius:20px;
        background: conic-gradient(from 90deg at 50% 50%, var(--c-blue), var(--c-teal), var(--c-green), var(--c-yellow), var(--c-orange), var(--c-pink), var(--c-purple), var(--c-blue));
        filter: blur(18px);
        opacity:.25;
        z-index:0;
      }
      .hero > *{ position:relative; z-index:1; }
      .hero .t1{ font-size: 34px; font-weight: 900; letter-spacing:.3px; }
      .hero .t2{ color:#D7E4FF; opacity:.98; }
      .ribbon{ height:6px; background:linear-gradient(90deg,var(--c-blue),var(--c-teal),var(--c-green),var(--c-yellow),var(--c-orange),var(--c-pink),var(--c-purple)); border-radius:999px; opacity:.9; margin:8px 0 2px 0; }

      .kpi{
        border-radius: 16px; padding: 16px 16px 12px 16px;
        border: 1px solid var(--glass-2); box-shadow: 0 16px 34px rgba(0,0,0,.45); font-weight: 800;
      }
      .kpi .big{ font-size: 26px; line-height:1; margin-top: 4px; font-weight: 900; }
      .kpi .sub{ font-size: 11px; opacity: .95; margin-top: 4px; font-weight: 700; }
      .kpi .label{ font-size: 13px; opacity: .98; font-weight: 800; letter-spacing: .3px; }
      .kpi-blue{   background: radial-gradient(120% 120% at 0% 0%, rgba(124,180,255,.55), transparent 60%), rgba(124,180,255,.12); }
      .kpi-green{  background: radial-gradient(120% 120% at 100% 0%, rgba(52,211,153,.55), transparent 60%), rgba(52,211,153,.12); }
      .kpi-pink{   background: radial-gradient(120% 120% at 0% 100%, rgba(236,72,153,.55), transparent 60%), rgba(236,72,153,.12); }
      .kpi-orange{ background: radial-gradient(120% 120% at 100% 100%, rgba(251,146,60,.55), transparent 60%), rgba(251,146,60,.12); }
      .glow-blue{   box-shadow: 0 0 0 2px rgba(124,180,255,.25) inset; }
      .glow-green{  box-shadow: 0 0 0 2px rgba(52,211,153,.25) inset; }
      .glow-pink{   box-shadow: 0 0 0 2px rgba(236,72,153,.25) inset; }
      .glow-orange{ box-shadow: 0 0 0 2px rgba(251,146,60,.25) inset; }

      .compact-table .row{ display:flex; gap:12px; justify-content:space-between; padding:8px 0; border-bottom:1px solid var(--glass-2); font-size:13px; }
      .compact-table .row:last-child{ border-bottom:0; }
      .pill{ display:inline-block; padding:2px 8px; border-radius:999px; background: rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.16); font-size:11px; font-weight:700; }

      .cal-head{ text-align:center; font-weight:900; font-size:14px; letter-spacing:.4px; margin-bottom:4px; }
      .cal-weekday{ font-weight:800; text-align:center; padding:4px 0; opacity:.95; font-size:11px; }
      .cal-cell{ border-radius: 10px; border: 1px solid var(--glass-2); background: rgba(255,255,255,.05); padding: 6px 4px 8px 4px; text-align: center; min-height: 46px; }
      .cal-empty{ background: transparent; border: 1px dashed rgba(255,255,255,.06); }
      .cal-daynum{ font-weight:800; font-size:13px; margin-bottom:4px; }
      .today-ring{ box-shadow: 0 0 0 2px var(--c-blue) inset, 0 0 18px rgba(124,180,255,.25); }
      .is-sat{ background: linear-gradient(180deg, rgba(167,139,250,.18), rgba(167,139,250,.05)); }
      .is-sun{ background: linear-gradient(180deg, rgba(236,72,153,.18), rgba(236,72,153,.05)); }
      .heat-1 .dot{ background: var(--c-green); }
      .heat-2 .dot{ background: var(--c-orange); }
      .heat-3 .dot{ background: var(--c-pink); }
      .dot{ width:7px; height:7px; border-radius:50%; margin:0 auto; box-shadow:0 0 10px rgba(255,255,255,.18); }

      .card-title{ display:flex; align-items:center; gap:10px; font-weight:900; letter-spacing:.3px; }
      .card-chip{ width:9px; height:18px; border-radius:3px; background: linear-gradient(180deg, var(--c-teal), var(--c-blue)); box-shadow: 0 0 10px rgba(45,212,191,.45); }
      .card-chip.pink{   background: linear-gradient(180deg, var(--c-pink), var(--c-purple)); box-shadow: 0 0 10px rgba(236,72,153,.45); }
      .card-chip.orange{ background: linear-gradient(180deg, var(--c-orange), var(--c-yellow)); box-shadow: 0 0 10px rgba(251,146,60,.45); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Services / Data ----------
pid = st.session_state["auth_user"]
psvc = PatientService()
asvc = AppointmentService()
auth_svc = AuthService()
esvc = EmergencyService()
msvc = MessagingService()

profile = psvc.get(pid) or {}
appts = asvc.list_by_patient(pid) or []
surveys = psvc.get_surveys(pid) or []
logins = auth_svc.get_login_history(pid, limit=8) or []
threads = msvc.list_threads_by_patient(pid) or []
open_threads = [t for t in threads if t.get("status") == "open"]
calls = esvc.list_by_patient(pid) or []

# ---------- Helpers ----------
def _to_dt(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def _appts_by_day_map(appts_list):
    m: dict[date, list] = {}
    for a in appts_list:
        dt = _to_dt(a.get("dt", ""))
        if not dt:
            continue
        m.setdefault(dt.date(), []).append(a)
    return m

appts_map = _appts_by_day_map(appts)

# ---------- Header + Emergency ----------
left, right = st.columns([0.70, 0.30], gap="large")
with left:
    st.markdown(
        """
        <div class="hero">
          <div class="t1">Your Dashboard</div>
          <div class="t2">Snapshot of your health & activity</div>
          <div class="ribbon"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with right:
    with card("Quick actions"):
        if st.button("🚨 Emergency Call Now", type="primary", use_container_width=True):
            patient_name = profile.get("name", "")
            db = read_db()
            users = db.get("users") or {}
            u = users.get(pid) or {}
            candidate_room = ""
            if profile.get("room"):
                candidate_room = str(profile.get("room"))
            else:
                sec_q = str(u.get("sec_q") or "")
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
            st.success(f"Emergency sent • ID: {call_id}") if ok else st.error(str(call_id))

# ---------- KPI Row ----------
c1, c2, c3, c4 = st.columns(4, gap="large")
now_iso = datetime.now().isoformat()
upcoming = [a for a in appts if a.get("dt", "") >= now_iso]
next_dt = upcoming[0]["dt"] if upcoming else "—"

with c1:
    st.markdown(
        f"""
        <div class="kpi kpi-blue glow-blue">
          <div class="label">Appointments</div>
          <div class="big">{len(upcoming)}</div>
          <div class="sub">Next: {next_dt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
        <div class="kpi kpi-green glow-green">
          <div class="label">Messages</div>
          <div class="big">{len(open_threads)}</div>
          <div class="sub">Open conversations</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
surv7 = [s for s in surveys if (s.get("ts","")[:10] >= (date.today().fromordinal(date.today().toordinal()-6)).isoformat())]
with c3:
    st.markdown(
        f"""
        <div class="kpi kpi-pink glow-pink">
          <div class="label">Daily Surveys</div>
          <div class="big">{len(surv7)}</div>
          <div class="sub">Last 7 days</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
calls7 = [c for c in calls if c.get("ts","")[:10] >= (date.today().fromordinal(date.today().toordinal()-6)).isoformat()]
with c4:
    st.markdown(
        f"""
        <div class="kpi kpi-orange glow-orange">
          <div class="label">Emergency Calls</div>
          <div class="big">{len(calls7)}</div>
          <div class="sub">Last 7 days</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Middle row: Trend (left) + Compact Month Calendar (right) ----------
left2, right2 = st.columns([0.60, 0.40], gap="large")

with left2:
    with card("Well-being trend (last 90 days)"):
        if surveys:
            df = pd.DataFrame(surveys)
            df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
            df = df.dropna(subset=["ts"])
            df["day"] = df["ts"].dt.date
            if "pain" in df.columns:
                trend = (
                    df.groupby("day")["pain"]
                    .mean()
                    .reset_index()
                    .sort_values("day")
                )
                trend = trend[trend["day"] >= date.today() - pd.Timedelta(days=90)]
                trend = trend.rename(columns={"day": "Date", "pain": "Average Pain"})

                # --- Custom colorful Altair chart (tight + on-brand) ---
                base = alt.Chart(trend).encode(
                    x=alt.X(
                        "Date:T",
                        axis=alt.Axis(
                            labelColor="#EAF2FF",
                            title=None,
                            grid=True,
                            gridColor="rgba(255,255,255,0.08)",
                            gridDash=[2,4],
                            tickColor="rgba(255,255,255,0.25)",
                            domainColor="rgba(255,255,255,0.25)",
                            labelFontSize=11
                        )
                    ),
                    y=alt.Y(
                        "Average Pain:Q",
                        scale=alt.Scale(domain=[0,10], nice=False),
                        axis=alt.Axis(
                            labelColor="#EAF2FF",
                            title=None,
                            grid=True,
                            gridColor="rgba(255,255,255,0.08)",
                            gridDash=[2,4],
                            tickColor="rgba(255,255,255,0.25)",
                            domainColor="rgba(255,255,255,0.25)",
                            labelFontSize=11
                        )
                    ),
                    tooltip=[
                        alt.Tooltip("Date:T", title="Date"),
                        alt.Tooltip("Average Pain:Q", format=".1f", title="Avg pain")
                    ],
                )

                area = base.mark_area(
                    interpolate="monotone",
                    opacity=0.35,
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            {"offset": 0, "color": "#2DD4BF"},
                            {"offset": 1, "color": "#7CB4FF"},
                        ],
                        x1=1, x2=1, y1=0, y2=1
                    )
                )

                line = base.mark_line(
                    interpolate="monotone",
                    stroke="#7CB4FF",
                    strokeWidth=3
                )

                points = base.mark_point(
                    filled=True,
                    size=55,
                    fill="#A78BFA",
                    stroke="#0B1329",
                    strokeWidth=1.2
                )

                chart = (area + line + points).properties(
                    height=220, padding={"left": 8, "right": 8, "top": 6, "bottom": 4},
                    background="rgba(0,0,0,0)"
                ).configure_view(
                    strokeWidth=0
                )

                st.altair_chart(chart, use_container_width=True)
                st.caption("Average reported pain per day (0 = none, 10 = worst).")
            else:
                st.info("No pain data in surveys yet.")
        else:
            st.info("No survey entries yet.")

with right2:
    with card("Calendar (this month)"):
        today = date.today()
        y, m = today.year, today.month

        st.markdown(f"<div class='cal-head'>{date(y, m, 1).strftime('%B %Y')}</div>", unsafe_allow_html=True)

        wd = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        cols = st.columns(7)
        for i, name in enumerate(wd):
            with cols[i]:
                st.markdown(f"<div class='cal-weekday'>{name}</div>", unsafe_allow_html=True)

        matrix = cal.Calendar(firstweekday=0).monthdayscalendar(y, m)

        for week in matrix:
            cols = st.columns(7)
            for i, d in enumerate(week):
                with cols[i]:
                    if d == 0:
                        st.markdown("<div class='cal-cell cal-empty'>&nbsp;</div>", unsafe_allow_html=True)
                        continue
                    this_day = date(y, m, d)
                    is_today = (this_day == today)
                    ring = " today-ring" if is_today else ""
                    weekend_cls = " is-sat" if i == 5 else (" is-sun" if i == 6 else "")
                    count = len(appts_map.get(this_day, []))
                    heat = "heat-1" if count == 1 else ("heat-2" if 2 <= count <= 3 else ("heat-3" if count >= 4 else ""))
                    dot_html = "<div class='dot'></div>" if count else "&nbsp;"

                    st.markdown(
                        f"""
                        <div class='cal-cell{ring}{weekend_cls} {heat}'>
                          <div class='cal-daynum'>{d}</div>
                          {dot_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.caption("• Dot color intensity reflects number of appointments (green < orange < pink). Weekends are lightly tinted.")

# ---------- Bottom row ----------
col_l, col_r = st.columns([0.60, 0.40], gap="large")

with col_l:
    with card("Today's appointments"):
        st.markdown("<div class='card-title'><span class='card-chip'></span>Today's Schedule</div>", unsafe_allow_html=True)
        todays = []
        for a in appts:
            dt = _to_dt(a.get("dt",""))
            if dt and dt.date() == date.today():
                todays.append({
                    "Time": dt.strftime("%I:%M %p").lstrip("0"),
                    "Note": a.get("note",""),
                    "ID": a.get("id","")
                })
        if not todays:
            st.caption("No appointments today.")
        else:
            st.dataframe(pd.DataFrame(todays), use_container_width=True, hide_index=True)

with col_r:
    with card("Recent emergency calls"):
        st.markdown("<div class='card-title'><span class='card-chip orange'></span>Latest Calls</div>", unsafe_allow_html=True)
        if not calls:
            st.caption("No emergency calls.")
        else:
            st.markdown('<div class="compact-table">', unsafe_allow_html=True)
            for c in calls[:6]:
                st.markdown(
                    f"""
                    <div class="row">
                      <div><b>{c.get('id','—')}</b><br><span class="muted">{c.get('ts','—')}</span></div>
                      <div><span class="pill">{(c.get('priority','') or '').title()}</span></div>
                      <div><span class="pill">{(c.get('status','open') or '').title()}</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)
