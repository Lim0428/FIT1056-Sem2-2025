# pages/3_📅_Appointments.py
import streamlit as st
from datetime import datetime, date, time, timedelta
import pandas as pd

from components.ui import apply_theme, page_header, card, require_auth
from app.appointments import AppointmentService
from app.storage import read_db  # to check global slot availability

# ── Page config / theme ───────────────────────────────────────────────────────
st.set_page_config(page_title="Appointments", page_icon="📅", layout="wide")
apply_theme()
require_auth()
page_header("Appointments", "Book and view your appointments", "📅")

svc = AppointmentService()
pid = st.session_state["auth_user"]

# ── Booking window / step size ────────────────────────────────────────────────
SLOT_MINUTES = 30          # 30-minute steps (matches your screenshot)
START_HOUR   = 8           # first slot 08:00
END_HOUR     = 20          # last *start* shown is 19:30

# ── Helpers ───────────────────────────────────────────────────────────────────
def all_times_for_day(d: date) -> list[datetime]:
    """Generate all slot start times in the working window for a given day."""
    cur = datetime.combine(d, time(START_HOUR, 0))
    end = datetime.combine(d, time(END_HOUR, 0))
    out = []
    while cur < end:
        out.append(cur)
        cur += timedelta(minutes=SLOT_MINUTES)
    return out

def taken_set_for_date(d: date) -> set[str]:
    """Return ISO minute strings for all globally booked slots on that date."""
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

# ── Book appointment ──────────────────────────────────────────────────────────
with card("Book appointment"):
    today = date.today()

    # Date picker (past dates disabled)
    d = st.date_input("Date", value=today, min_value=today, format="YYYY/MM/DD")

    # Build available times for chosen day:
    #  - 30-minute steps in working window
    #  - hide past times if booking "today"
    #  - hide already-booked slots
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

    # Helper text like your screenshot
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

# ── Your appointments (simple table) ──────────────────────────────────────────
with card("Your appointments"):
    appts = list(reversed(svc.list_by_patient(pid)))
    if not appts:
        st.info("No appointments yet.")
    else:
        df = to_table_df(appts)
        # default to upcoming
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
