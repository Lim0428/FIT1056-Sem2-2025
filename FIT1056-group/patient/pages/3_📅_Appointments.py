# pages/3_📅_Appointments.py
import streamlit as st
from datetime import datetime, date, time, timedelta
import calendar as pycal

from components.ui import apply_theme, page_header, card, require_auth
from app.appointments import AppointmentService
from app.storage import read_db  # for global availability checks

# ── Page config / theme ───────────────────────────────────────────────────────
st.set_page_config(page_title="Appointments", page_icon="📅", layout="centered")
apply_theme()
require_auth()
page_header("Appointments", "Book and view your appointments", "📅")

svc = AppointmentService()
pid = st.session_state["auth_user"]

# ── Calendar parameters ───────────────────────────────────────────────────────
SLOT_MINUTES = 30
START_HOUR   = 9
END_HOUR     = 17  # end-exclusive (last start 16:30)

# ── Helpers ───────────────────────────────────────────────────────────────────
def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())

def all_slots_for_day(d: date):
    cur = datetime.combine(d, time(START_HOUR, 0))
    end = datetime.combine(d, time(END_HOUR, 0))
    out = []
    while cur < end:
        out.append(cur)
        cur += timedelta(minutes=SLOT_MINUTES)
    return out

def taken_set_for_week(monday: date) -> set[str]:
    """ISO-to-minutes strings for all booked times this week (global)."""
    db = read_db()
    start_dt = datetime.combine(monday, time.min)
    end_dt   = start_dt + timedelta(days=7)
    taken = set()
    for a in db.get("appointments", []):
        try:
            dt = datetime.fromisoformat(a.get("dt", ""))
            if start_dt <= dt < end_dt:
                taken.add(dt.isoformat(timespec="minutes"))
        except Exception:
            pass
    return taken

def fmt_day_label(d: date) -> str:
    return f"{pycal.day_name[d.weekday()]}<br><small>{d.strftime('%d %b')}</small>"

def label_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")

def slot_key(dt: datetime) -> str:
    return f"slot_{dt.strftime('%Y%m%d_%H%M')}"

# ── Slot picker (buttons styled like your design — no navigation) ─────────────
with card("Book appointment"):
    SEL_KEY = "selected_slot_iso"
    selected_iso = st.session_state.get(SEL_KEY, "")

    # Week navigation
    today = date.today()
    if "wk_start" not in st.session_state:
        st.session_state.wk_start = week_start(today)

    nav_l, nav_c, nav_r = st.columns([1, 2, 1])
    with nav_l:
        if st.button("◀️  Prev week"):
            st.session_state.wk_start -= timedelta(days=7)
    with nav_c:
        picked = st.date_input("Week of", value=st.session_state.wk_start, format="YYYY/MM/DD")
        st.session_state.wk_start = week_start(picked)
    with nav_r:
        if st.button("Next week  ▶️"):
            st.session_state.wk_start += timedelta(days=7)

    monday = st.session_state.wk_start
    full_days = [monday + timedelta(days=i) for i in range(7)]
    full_labels = [fmt_day_label(d) for d in full_days]

    # Options
    opt1, opt2 = st.columns([1, 1])
    with opt1:
        density = st.select_slider(
            "Density",
            options=["Comfortable", "Compact", "Extra compact", "Super tight"],
            value="Super tight",
            help="Adjust slot size and spacing."
        )
    with opt2:
        weekdays_only = st.toggle("Weekdays only (Mon–Fri)", value=True)

    days = full_days[:5] if weekdays_only else full_days
    labels = full_labels[:5] if weekdays_only else full_labels
    day_count = len(days)

    # Availability & rows
    taken = taken_set_for_week(monday)
    time_rows = all_slots_for_day(monday)

    # Density → CSS vars (keep your compact look)
    if density == "Comfortable":
        gap_x, gap_y = "10px", "10px"; pad = "8px 10px"; fpx = "13px"; radius="10px"; min_h="36px"
    elif density == "Compact":
        gap_x, gap_y = "8px", "6px";  pad = "6px 8px";  fpx = "12px"; radius="9px";  min_h="32px"
    elif density == "Extra compact":
        gap_x, gap_y = "6px", "4px";  pad = "5px 7px";  fpx = "11px"; radius="8px";  min_h="30px"
    else:  # Super tight
        gap_x, gap_y = "5px", "2px";  pad = "3px 6px";  fpx = "10px"; radius="7px";  min_h="28px"

    # CSS: grid headers + buttons styled as your blue chips (no anchor links)
    st.markdown(f"""
    <style>
      .wk-grid {{
        display: grid;
        grid-template-columns: repeat({day_count}, 1fr);
        column-gap: {gap_x};
        row-gap: {gap_y};
        align-items: center;
      }}
      .wk-cell {{ text-align: center; }}
      .wk-head {{ font-weight: 800; margin-bottom: {gap_y}; }}
      .wk-head small {{ color:#6B7280; }}

      /* Make Streamlit buttons match your chip style */
      .slot-btn > button {{
        width: 100%;
        padding: {pad};
        min-height: {min_h};
        border-radius: {radius};
        border: 1px solid #1B65DC;
        background: #1B65DC;
        color: #FFFFFF;
        font-weight: 700;
        font-size: {fpx};
        line-height: 1.1;
      }}
      .slot-btn > button:hover {{ filter: brightness(1.06); }}

      /* Disabled (taken) */
      .slot-taken > button {{
        background:#F3F5FA !important; color:#98A2B3 !important; border-color:#E5EAF5 !important;
      }}

      /* Selected */
      .slot-selected > button {{
        background:#0A47A7 !important; border-color:#0A47A7 !important;
        color:#FFFFFF !important; box-shadow:0 3px 8px rgba(10,71,167,.25);
      }}
    </style>
    """, unsafe_allow_html=True)

    # Header row
    st.markdown(
        '<div class="wk-grid">' +
        "".join(f'<div class="wk-cell wk-head">{lab}</div>' for lab in labels) +
        "</div>",
        unsafe_allow_html=True
    )

    # Time rows (build grid row-by-row; each cell has one Streamlit button)
    for base_dt in time_rows:
        # open a container that has the grid
        st.markdown(f'<div class="wk-grid">', unsafe_allow_html=True)
        # create a Streamlit column for each day to place the button
        cols = st.columns(day_count)
        for i, d in enumerate(days):
            dt = datetime.combine(d, base_dt.time())
            iso_min = dt.isoformat(timespec="minutes")
            is_taken = iso_min in taken
            is_selected = (selected_iso == iso_min)

            with cols[i]:
                # wrapper div applies the right CSS class to the internal button
                klass = "slot-btn"
                if is_taken:
                    klass = "slot-btn slot-taken"
                elif is_selected:
                    klass = "slot-btn slot-selected"

                st.markdown(f'<div class="{klass}">', unsafe_allow_html=True)
                if st.button(label_time(dt), key=slot_key(dt), disabled=is_taken):
                    st.session_state[SEL_KEY] = iso_min
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Note + Book
    note = st.text_input("Note / reason", key="appt_note")
    chosen_dt = datetime.fromisoformat(st.session_state[SEL_KEY]) if st.session_state.get(SEL_KEY) else None

    if st.button("Book", type="primary"):
        if not chosen_dt:
            st.error("Please select a time slot.")
        elif chosen_dt.isoformat(timespec="minutes") in taken:
            st.error("That slot was just booked. Please choose another.")
        else:
            ok, msg = svc.book(pid, chosen_dt, note)
            if ok:
                st.success(f"Booked: {msg}")
                st.session_state.pop(SEL_KEY, None)   # clear selection after success
            else:
                st.error(msg)

# ── Your appointments ─────────────────────────────────────────────────────────
with card("Your appointments"):
    appts = list(reversed(svc.list_by_patient(pid)))
    if not appts:
        st.info("No appointments yet.")
    else:
        for a in appts:
            try:
                when = datetime.fromisoformat(a["dt"])
                label = when.strftime("%a, %d %b %Y — %I:%M %p").lstrip("0")
            except Exception:
                label = a["dt"]
            st.write(f"• **{label}** — {a.get('note','(no note)')}  (ID: {a['id']})")
