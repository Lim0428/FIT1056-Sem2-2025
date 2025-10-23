# doctor_name_components/widgets.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

PRIMARY = "#2E5AAC"
ACCENT  = "#30C48D"
MUTED   = "#9AA4B2"
# --- add back this helper used by tables.py ---


def timestamp_label(dt_iso: str) -> str:
    """
    Format ISO datetime like '2025-10-23T10:30:00' to '23 Oct 2025 • 10:30'.
    Falls back gracefully if parse fails.
    """
    try:
        dt = datetime.fromisoformat(str(dt_iso).replace("Z",""))
        return dt.strftime("%d %b %Y • %H:%M")
    except Exception:
        return str(dt_iso) if dt_iso else "-"

def kpi_stat(label, value):
    st.markdown(
        f"""
        <div style="
            background: rgba(255,255,255,0.06);
            border:1px solid rgba(255,255,255,0.10);
            border-radius: 999px;
            padding: 8px 14px;
            display:flex; align-items:center; justify-content:space-between;">
            <div style="font-size:12px;color:{MUTED};">{label}</div>
            <div style="font-size:22px;font-weight:800;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def revenue_chart(labels, values,
                  x_label="Revenue (RM)", y_label="Year",
                  bg_color="#0A1930", bar_color="#4FC3F7", grid=True):
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    import numpy as np
    from matplotlib.ticker import FuncFormatter

    y_labels = list(labels)
    x_vals   = list(values)
    n = len(x_vals)

    # --- Colors ---
    text_color = "#FFFFFF"
    grid_color = "#2A3750"

    fig, ax = plt.subplots(figsize=(7.2, 3.6), facecolor="none")
    ax.set_facecolor(bg_color)

    # Positions (top-to-bottom) and uniform bar thickness
    y_pos  = np.arange(n)[::-1]   # reverse so first label is at the top
    height = 0.6                  # constant thickness
    radius = height / 2

    # Draw rounded bars
    for y, w in zip(y_pos, x_vals):
        ax.add_patch(FancyBboxPatch(
            (0, y - height/2),     # x, y(lower-left)
            w, height,             # width, height
            boxstyle=f"round,pad=0,rounding_size={radius}",
            linewidth=0,
            facecolor=bar_color
        ))

    # --- Axis range & padding so top/bottom bars aren't clipped ---
    ax.set_ylim(-0.5, n - 0.5)    # critical: reserves half a bar above/below
    ax.set_xlim(0, max(x_vals) * 1.1)

    # Ticks/labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels, color=text_color, fontsize=10)
    ax.set_xlabel(x_label, color=text_color, labelpad=8, fontsize=11, weight="bold")
    ax.set_ylabel(y_label, color=text_color, labelpad=8, fontsize=11, weight="bold")

    # Grid & formatting
    if grid:
        ax.xaxis.grid(True, color=grid_color, linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _ : f"{int(x):,}"))

    # Clean up
    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="x", colors=text_color, length=0, labelsize=9)
    ax.tick_params(axis="y", length=0, labelsize=9)

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)


def today_appointments_list(store):
    # Pull upcoming today; if none, show demo items
    appts = store.list_upcoming_appointments(limit=5)
    rows = []
    if not appts:
        # demo list (time ascending)
        rows = [
            {"name":"Ucok Bendart","tag":"First Visit","time":"10:00 AM"},
            {"name":"Mac Jansen","tag":"Consultation","time":"12:00 PM"},
            {"name":"Anastasiya Gemash","tag":"Consultation","time":"11:00 AM"},
            {"name":"Jimmi Jazz","tag":"First Visit","time":"1:00 PM"},
        ]
    else:
        for a in appts:
            t = a["start"][11:16]
            h, m = t.split(":")
            hh = int(h)
            suffix = "AM" if hh < 12 else "PM"
            hh12 = hh if 1 <= hh <= 12 else (hh-12 if hh>12 else 12)
            rows.append({
                "name": f"Patient #{a['patient_id']}",
                "tag": a.get("reason","Consultation") or "Consultation",
                "time": f"{hh12}:{m} {suffix}"
            })
    for r in rows:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:10px; padding:8px 6px; border-bottom:1px solid rgba(255,255,255,0.08);">
              <div style="width:36px;height:36px;border-radius:50%;background:#1f2937;display:flex;align-items:center;justify-content:center;">👤</div>
              <div style="flex:1;">
                <div style="font-weight:600;">{r['name']}</div>
                <div style="font-size:12px;color:{ACCENT};">{r['tag']}</div>
              </div>
              <div style="font-size:12px;color:{MUTED};">{r['time']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("<div style='text-align:right;'><a style='font-size:12px;color:#cbd5e1' href='#'>See All</a></div>", unsafe_allow_html=True)

def profile_card(store):
    name = store.doctor_display_name()
    role = getattr(st.session_state, "auth", {}).get("user", {}).get("specialty", "Doctor")
    avg, n = store.doctor_average_rating()
    # use assigned/consented patients as the “average patient” count on card
    total_patients = store.count_assigned_patients()

    st.markdown(
        f"""
        <div style="background: rgba(255,255,255,0.06); 
                    border:1px solid rgba(255,255,255,0.10); 
                    border-radius: 18px; padding: 14px;">
            <div style="font-weight:700;margin-bottom:6px;">Your Profile</div>
            <div style="display:flex; align-items:center; gap:12px;">
              <div style="width:56px;height:56px;border-radius:50%;background:#1f2937;display:flex;align-items:center;justify-content:center;font-size:26px;">🧑‍⚕️</div>
              <div>
                <div style="font-weight:700;">{name}</div>
                <div style="font-size:12px;color:{MUTED};">{role}</div>
              </div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px;">
              <div style="background:#a3e63522;border:1px solid #a3e63544;border-radius:12px;padding:10px;text-align:center;">
                <div style="font-size:22px;font-weight:800;">{avg if n else '—'}</div>
                <div style="font-size:12px;color:{MUTED};">Overall Rating{f' ({n})' if n else ''}</div>
              </div>
              <div style="background:#a3e63522;border:1px solid #a3e63544;border-radius:12px;padding:10px;text-align:center;">
                <div style="font-size:22px;font-weight:800;">{total_patients}</div>
                <div style="font-size:12px;color:{MUTED};">Patients</div>
              </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def messages_list(store):
    # Demo messages (replace with real threads if available)
    threads = []  # you can fill from store.list_threads(store) if needed
    if not threads:
        rows = [
            ("Devon Lane", "You’ve got some kind of a sto…", "09:10"),
            ("Jack Randall", "How are you feeling?", "08:00"),
            ("Shell Wong", "OK, Got it! 😊", "04:12"),
            ("Aura Kasih", "You’re welcome.🙏", "17/12/2023"),
            ("Jonathan Wacid", "Thank you doctor!", "12/08/2023"),
        ]
    else:
        # flatten your threads here
        rows = []
    st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
          <div style="flex:1;"><input placeholder="Search for chats" style="width:100%;padding:10px;border-radius:10px;border:1px solid rgba(255,255,255,0.15);background:#0D1422;color:#E6E6E6;" /></div>
          <div style="width:36px;height:36px;border-radius:10px;background:#0D1422;border:1px solid rgba(255,255,255,0.15);display:flex;align-items:center;justify-content:center;">＋</div>
        </div>
    """, unsafe_allow_html=True)
    for name, text, when in rows:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:10px; padding:10px; border-bottom:1px solid rgba(255,255,255,0.08);">
              <div style="width:40px;height:40px;border-radius:50%;background:#1f2937;display:flex;align-items:center;justify-content:center;">💬</div>
              <div style="flex:1;">
                <div style="font-weight:600;">{name}</div>
                <div style="font-size:12px;color:{MUTED};">{text}</div>
              </div>
              <div style="font-size:11px;color:{MUTED};">{when}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

def duty_hour_strip():
    """Render the 7-day duty strip as real HTML (no Markdown escaping)."""
    from datetime import datetime, timedelta
    from streamlit.components.v1 import html  # <- important

    today = datetime.now().date()
    start = today - timedelta(days=today.weekday())  # Monday
    days = [start + timedelta(days=i) for i in range(7)]

    cards = []
    for d in days:
        is_today = (d == today)
        bg   = "#1f2937" if is_today else "#0D1422"
        txt  = "#ffffff" if is_today else "#E6E6E6"
        bord = "rgba(255,255,255,0.18)" if is_today else "rgba(255,255,255,0.12)"
        cards.append(f"""
          <div style="
              border-radius:12px; padding:10px; text-align:center;
              background:{bg}; color:{txt}; border:1px solid {bord};
            ">
            <div style="font-size:11px;color:#9AA4B2;">{d.strftime('%a')}</div>
            <div style="font-weight:700;">{d.strftime('%d')}</div>
          </div>
        """)

    html_content = f"""
      <div style="display:grid; grid-template-columns:repeat(7,1fr); gap:10px;">
        {''.join(cards)}
      </div>
    """
    # Render as raw HTML so Streamlit doesn't escape it
    html(html_content, height=110, scrolling=False)


def appointment_history_list():
    rows = [
        ("Medical Checkup", "May 22 • 10–11 AM"),
        ("Screening", "April 10 • 9–9:30 AM"),
        ("Chat Consultation", "May 22 • 12–12:30 AM"),
        ("Video call Consultation", "Jan 14 • 10–12 AM"),
    ]
    for title, sub in rows:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:10px; padding:10px; border-bottom:1px solid rgba(255,255,255,0.08);">
              <div style="width:36px;height:36px;border-radius:10px;background:#0D1422;border:1px solid rgba(255,255,255,0.12);display:flex;align-items:center;justify-content:center;">📌</div>
              <div>
                <div style="font-weight:600;">{title}</div>
                <div style="font-size:12px;color:{MUTED};">{sub}</div>
              </div>
              <div style="margin-left:auto;font-size:12px;color:{MUTED};">View</div>
            </div>
            """,
            unsafe_allow_html=True
        )

def overall_appointment_card():
    st.markdown(
        """
        <div style="margin-top:12px; background:#0A0F18; border:1px solid rgba(255,255,255,0.08);
                    border-radius:16px; padding:14px;">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <div style="width:26px;height:26px;border-radius:50%;background:#0D1422;display:flex;align-items:center;justify-content:center;">🟢</div>
              <div>Overall Appointment</div>
            </div>
            <div style="font-size:12px;color:#a3e635;">+ 6.91%</div>
          </div>
          <div style="height:60px; background:linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02)); border-radius:8px;"></div>
          <div style="margin-top:10px; font-weight:800;">5,287.02</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def screen_time_card(card_title="Duty Hour", mode_key="duty_mode"):
    """
    iOS Screen Time–style card without illegal nested columns:
      • Single columns row for Week/Day buttons
      • Big headline time
      • Weekly + hourly charts
    """
    import streamlit as st
    import numpy as np
    import matplotlib.pyplot as plt
    from datetime import datetime
    # state
    if mode_key not in st.session_state:
        st.session_state[mode_key] = "Day"

    # centered Week/Day buttons using a SINGLE columns row
    c = st.columns([3,1,1,3])
    with c[1]:
        if st.button("Week", use_container_width=True, key=f"{mode_key}_week"):
            st.session_state[mode_key] = "Week"
    with c[2]:
        if st.button("Day", use_container_width=True, key=f"{mode_key}_day"):
            st.session_state[mode_key] = "Day"

    # title + subtitle
    st.markdown(f"**{card_title}**")
    st.caption("Avg Duty Hour 57 h")

    # headline value (demo)
    total_minutes = 5*60 + 26 if st.session_state[mode_key] == "Day" else 27*60
    st.markdown(
        f"<div style='font-size:40px;font-weight:800;margin:2px 0 8px 0;'>{total_minutes//60}h {total_minutes%60}m</div>",
        unsafe_allow_html=True
    )

    # ------- Weekly chart -------
    days = list("MTWTFSS")
    vals = np.array([2.5, 4.2, 3.1, 2.8, 3.0, 5.0, 3.5])  # demo hours
    today_idx = datetime.now().weekday()

    fig1, ax1 = plt.subplots(figsize=(6.8, 1.9), facecolor="none")
    ax1.set_facecolor("#0A0F18")
    colors = ["#9CA3AF"]*7
    colors[today_idx] = "#38BDF8"
    ax1.bar(range(7), vals, color=colors, edgecolor="none", width=0.6)
    ax1.set_xticks(range(7))
    ax1.set_xticklabels(days, color="#E6E6E6")
    ax1.set_yticks([0,1,2,3])
    ax1.yaxis.grid(True, color="#263043", linestyle="--", linewidth=0.6, alpha=0.7)
    ax1.tick_params(axis="y", colors="#9AA4B2")
    for sp in ["top","right","left","bottom"]:
        ax1.spines[sp].set_visible(False)
    st.pyplot(fig1, use_container_width=True)

    # ------- Hourly chart -------
    hours = np.arange(24)
    base  = np.abs(np.sin(hours/3))*0.6
    base[(hours>=17)&(hours<=21)] += np.array([0.4,0.6,0.8,0.6,0.4])
    fig2, ax2 = plt.subplots(figsize=(6.8, 1.9), facecolor="none")
    ax2.set_facecolor("#0A0F18")
    ax2.bar(hours, base*60, color="#38BDF8", edgecolor="none", width=0.6)
    ax2.set_xticks([0,6,12,18])
    ax2.set_xticklabels(["00","06","12","18"], color="#E6E6E6")
    ax2.set_yticks([0,30,60])
    ax2.set_yticklabels(["0","30m","60m"], color="#9AA4B2")
    ax2.yaxis.grid(True, color="#263043", linewidth=0.6, alpha=0.7)
    for sp in ["top","right","left","bottom"]:
        ax2.spines[sp].set_visible(False)
    st.pyplot(fig2, use_container_width=True)

    # Legend (demo)
    st.markdown(
        """
        <div style="display:flex;gap:24px;margin-top:4px;">
          <div><span style="color:#38BDF8;font-weight:700;">Social</span> <span class="muted">3h 19m</span></div>
          <div><span style="color:#60A5FA;font-weight:700;">Creativity</span> <span class="muted">1h 32m</span></div>
          <div><span style="color:#F59E0B;font-weight:700;">Shopping & Food</span> <span class="muted">4m</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )
