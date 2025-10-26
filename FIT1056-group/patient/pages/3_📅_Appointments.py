# pages/3_📅_Appointments.py
import streamlit as st
from datetime import datetime, date, time, timedelta
import pandas as pd

from components.ui import apply_theme, card, require_auth   # (no page_header to avoid double header)
from app.appointments import AppointmentService
from app.storage import read_db  # to check global slot availability

# ── Page config / theme ───────────────────────────────────────────────────────
st.set_page_config(page_title="Appointments", page_icon="📅", layout="wide")
apply_theme()
require_auth()

# ── Colorful styling to match other pages (UI only) ───────────────────────────
st.markdown(
    """
    <style>
      :root{
        --bg:#0B1329; --bg2:#0A1124; --text:#F7FAFF; --muted:#CFE0FF;
        --c-blue:#7CB4FF; --c-teal:#2DD4BF; --c-green:#34D399; --c-pink:#EC4899;
        --c-orange:#FB923C; --c-purple:#A78BFA; --c-yellow:#FDE047;
        --field:#0F1A2E; --panel:#0D172B; --panel-border:rgba(255,255,255,.22);
        --hover:rgba(124,180,255,.18); --selected:rgba(124,180,255,.28);
      }
      [data-testid="stAppViewContainer"]{ background:var(--bg) !important; color:var(--text) !important; }
      section[data-testid="stSidebar"]{ background:var(--bg2) !important; color:var(--text) !important; }

      /* HERO header (same vibe as Dashboard/Daily Survey) */
      .ap-hero{
        margin-top:8px; margin-bottom:18px; padding:22px 26px;
        border-radius:20px;
        background:
          radial-gradient(100% 140% at 0% 0%, rgba(124,180,255,.35), transparent 60%),
          linear-gradient(135deg, #172947, #111B32 40%, #13203C);
        border:1px solid rgba(255,255,255,.14);
        box-shadow: 0 26px 60px rgba(0,0,0,.55);
      }
      .ap-hero h1{ margin:0; font-size:42px; font-weight:900; letter-spacing:.3px; color:#F8FBFF; }
      .ap-hero .sub{ color:#D7E4FF; opacity:.98; margin-top:6px; font-weight:600; }
      .ap-hero .bar{
        height:6px; width:100%; border-radius:999px; margin-top:14px;
        background: linear-gradient(90deg, var(--c-blue), var(--c-teal), var(--c-green),
                                    var(--c-yellow), var(--c-orange), var(--c-pink), var(--c-purple));
        box-shadow: 0 8px 24px rgba(124,180,255,.25);
      }

      /* Inputs & dropdowns — dark, readable */
      .stTextInput > div > div > input,
      .stTextArea textarea,
      .stDateInput > div > input{
        background: var(--field) !important;
        color:#EAF2FF !important;
        border:1px solid rgba(255,255,255,.20) !important;
      }
      [data-testid="stSelectbox"] div[data-baseweb="select"] > div{
        background: var(--field) !important;
        border: 1px solid rgba(255,255,255,.20) !important;
      }
      [data-testid="stSelectbox"] div[data-baseweb="select"] *{ color:#EAF2FF !important; }
      [data-testid="stSelectbox"] div[data-baseweb="select"] div[class*="placeholder"]{ color:#9FB0C3 !important; }
      [data-testid="stSelectbox"] svg{ color:#EAF2FF !important; fill:#EAF2FF !important; }

      /* Dropdown panel */
      div[data-baseweb="popover"] *{ color:#EAF2FF !important; }
      div[data-baseweb="popover"] div, div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li{ background: var(--panel) !important; }
      [role="listbox"]{ background:var(--panel) !important; border:1px solid var(--panel-border) !important; }
      [role="option"]{ color:#EAF2FF !important; }
      [role="option"]:hover{ background: var(--hover) !important; }
      [role="option"][aria-selected="true"]{ background: var(--selected) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# HERO
st.markdown(
    """
    <div class="ap-hero">
      <h1>Appointments</h1>
      <div class="sub">Book and view your appointments</div>
      <div class="bar"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

svc = AppointmentService()
pid = st.session_state["auth_user"]

# ── Booking window / step size ────────────────────────────────────────────────
SLOT_MINUTES = 30          # 30-minute steps (matches your original)
START_HOUR   = 8           # first slot 08:00
END_HOUR     = 20          # last *start* shown is 19:30

# ── Helpers (unchanged) ───────────────────────────────────────────────────────
def all_times_for_day(d: date) -> list[datetime]:
    cur = datetime.combine(d, time(START_HOUR, 0))
    end = datetime.combine(d, time(END_HOUR, 0))
    out = []
    while cur < end:
        out.append(cur)
        cur += timedelta(minutes=SLOT_MINUTES)
    return out

def taken_set_for_date(d: date) -> set[str]:
    db = read_db()
    starts = set()
    for a in db.get("appointments", []):
        try:
            dt = datetime.fromisoformat(a.get("dt", ""))
            if dt.date() == d:
                starts.add(dt.isoformat(timespec="minutes"))
        except Exception:
            pass
    return starts

def to_table_df(appts: list[dict]) -> pd.DataFrame:
    rows = []
    for a in appts:
        try:
            dt = datetime.fromisoformat(a["dt"])
            rows.append({
                "_dt": dt,
                "Date": dt.strftime("%a, %d %b %Y"),
                "Time": dt.strftime("%I:%M %p").lstrip("0"),
                "Note": a.get("note", ""),
                "ID": a.get("id", ""),
            })
        except Exception:
            rows.append({"_dt": None, "Date": a.get("dt",""), "Time": "", "Note": a.get("note",""), "ID": a.get("id","")})
    return pd.DataFrame(rows)

# ── Book appointment (ORIGINAL LOGIC) ─────────────────────────────────────────
with card("Book appointment"):
    today = date.today()

    # Date picker (past dates disabled)
    d = st.date_input("Date", value=today, min_value=today, format="YYYY/MM/DD")

    # Build available times for chosen day:
    all_slots = all_times_for_day(d)
    taken = taken_set_for_date(d)

    now = datetime.now()
    def allowed(dt: datetime) -> bool:
        if d == today and dt <= now.replace(second=0, microsecond=0):
            return False
        return dt.isoformat(timespec="minutes") not in taken

    avail_dts = [dt for dt in all_slots if allowed(dt)]
    time_labels = [dt.strftime("%H:%M") for dt in avail_dts]
    label_to_dt = {lab: dt for lab, dt in zip(time_labels, avail_dts)}

    # Time selector (only available choices shown)
    t_label = st.selectbox("Time", options=time_labels, index=0 if time_labels else None, placeholder="No available times")

    # Note
    note = st.text_input("Reason / note (optional)")

    # Helper text
    st.caption("Pick a date and time (30-minute steps). Past dates/times are disabled.")

    # Book
    if st.button("➕ Book", type="primary", disabled=not t_label):
        if not t_label:
            st.error("Please choose a time.")
        else:
            chosen_dt = label_to_dt[t_label]
            # Double-check availability just before booking
            if chosen_dt.isoformat(timespec="minutes") in taken_set_for_date(chosen_dt.date()):
                st.error("That slot was just booked. Please choose another time.")
            else:
                ok, msg = svc.book(pid, chosen_dt, note)
                if ok:
                    st.success(f"Booked: {msg}")
                else:
                    st.error(msg)

# ── Your appointments (ORIGINAL LOGIC) ────────────────────────────────────────
with card("Your appointments"):
    appts = list(reversed(svc.list_by_patient(pid)))
    if not appts:
        st.info("No appointments yet.")
    else:
        df = to_table_df(appts)
        now_dt = datetime.now()
        view = st.segmented_control("View", options=["Upcoming", "All", "Past"], default="Upcoming")
        if view == "Upcoming":
            show = df[df["_dt"].notna() & (df["_dt"] >= now_dt)].sort_values("_dt")
        elif view == "Past":
            show = df[df["_dt"].notna() & (df["_dt"] < now_dt)].sort_values("_dt", ascending=False)
        else:
            show = df.sort_values(["_dt"], ascending=[True])

        st.dataframe(
            show.drop(columns=["_dt"]),
            use_container_width=True,
            hide_index=True,
            height=min(380, 48 + 32 * max(1, len(show)))
        )
