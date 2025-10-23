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


def messages_panel(store):
    """
    Interactive dashboard message panel:
      • Case-insensitive search
      • Click a row to open conversation
      • Send a reply (writes to messages.json)
      • Mark resolved
      • (Optional) Simulate patient reply for testing
      • Threads sorted oldest -> newest so latest is at the bottom
    """
    import streamlit as st
    from datetime import datetime
    from doctor_name_services.messaging import list_threads, get_thread, add_message, mark_resolved

    # --- helpers ---
    def _parse_ts(s: str) -> datetime:
        try:
            return datetime.fromisoformat(str(s).replace("Z",""))
        except Exception:
            return datetime.min

    # --- search ---
    query = (st.text_input(
        "Search for chats",
        key="dash_msg_query",
        label_visibility="collapsed",
        placeholder="Search for chats",
    ) or "").strip().lower()

    # '+' new-thread placeholder (optional)
    cols = st.columns([1, 0.12])
    with cols[1]:
        st.button("+", use_container_width=True, key="dash_msg_new_btn")

    # --- data ---
    threads = list_threads(store) or []

    # normalize rows
    items = []
    for t in threads:
        msgs = t.get("messages") or []
        latest = msgs[-1] if msgs else {}
        preview = str(latest.get("text", "")).strip()
        name = t.get("name") or f"Patient #{t.get('patient_id','—')}"
        when = t.get("updated_at") or latest.get("timestamp") or ""
        items.append({
            "id": t.get("id"),
            "name": name,
            "preview": preview,
            "when": when,
        })

    # filter (case-insensitive)
    if query:
        items = [r for r in items if query in r["name"].lower() or query in r["preview"].lower()]

    # sort oldest -> newest so latest shows at the bottom
    items.sort(key=lambda r: _parse_ts(r["when"]))

    # --- selected thread state ---
    sel_key = "dash_selected_thread"
    if sel_key not in st.session_state and items:
        st.session_state[sel_key] = items[-1]["id"]  # default to newest

    # --- render list with clickable rows ---
    for r in items:
        dt = _parse_ts(r["when"])
        when_str = dt.strftime("%H:%M") if dt.date() == datetime.now().date() else dt.strftime("%d/%m/%Y")
        pressed = st.button(
            key=f"open_{r['id']}",
            label=f"{r['name']} • {when_str}\n{r['preview']}",
            use_container_width=True
        )
        # style the button like a row (CSS already makes buttons uniform)
        if pressed:
            st.session_state[sel_key] = r["id"]

    # divider
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # --- conversation view ---
    tid = st.session_state.get(sel_key)
    if not tid:
        return

    thr = get_thread(store, tid)
    if not thr:
        st.warning("Thread not found or not permitted.")
        return

    st.markdown(f"**Thread #{thr['id']}** • Patient #{thr['patient_id']} • Status: {thr.get('status','open')}")
    # render chat history (oldest → newest)
    msgs = thr.get("messages", [])
    for m in msgs:
        who = "Doctor" if m.get("sender_role") == "doctor" else "Patient"
        bubble_align = "flex-end" if who == "Doctor" else "flex-start"
        bubble_bg     = "#2E5AAC" if who == "Doctor" else "#0D1422"
        st.markdown(
            f"""
            <div style="display:flex; justify-content:{bubble_align}; margin:4px 0;">
              <div style="max-width:80%; padding:8px 12px; border-radius:12px;
                          background:{bubble_bg}; border:1px solid rgba(255,255,255,0.10);">
                <div style="font-size:12px; opacity:.8;">{who} • {m.get('timestamp','')}</div>
                <div style="white-space:pre-wrap;">{m.get('text','')}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()
    # reply box
    with st.form(f"reply_form_{tid}", clear_on_submit=True):
        txt = st.text_area("Reply", placeholder="Type your message…", height=80)
        c1, c2, c3 = st.columns([1,1,1])
        send = c1.form_submit_button("Send", use_container_width=True)
        resolve = c2.form_submit_button("Mark Resolved", use_container_width=True)
        simulate = c3.form_submit_button("Simulate Patient Reply (demo)", use_container_width=True)

        if send and txt.strip():
            add_message(store, tid, "doctor", txt.strip())
            st.success("Sent.")
            st.rerun()

        if resolve and thr.get("status") != "resolved":
            mark_resolved(store, tid)
            st.success("Thread marked resolved.")
            st.rerun()

        if simulate:
            add_message(store, tid, "patient", "Thanks doctor, noted.")
            st.info("Simulated patient reply added.")
            st.rerun()


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

# --- INTERACTIVE DUTY STRIP (Mon–Sun) + LINE CHART ---

def duty_hour_strip_interactive(state_key="duty_selected"):
    """
    Renders 7 pill buttons (Mon..Sun). Clicking a pill selects that day.
    Stores selection in st.session_state[state_key] and returns the selected date.
    """
    import streamlit as st
    from datetime import datetime, timedelta

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())  # Monday start
    days = [monday + timedelta(days=i) for i in range(7)]
    labels = [d.strftime("%a\n%d") for d in days]     # e.g., "Mon\n20"

    # default to today
    if state_key not in st.session_state:
        st.session_state[state_key] = today

    cols = st.columns(7)
    for i, c in enumerate(cols):
        d = days[i]
        is_sel = (st.session_state[state_key] == d)
        # visually mark selected via emoji dot (keeps code simple). Optional.
        label = labels[i] + ("  ●" if is_sel else "")
        with c:
            if st.button(label, use_container_width=True, key=f"duty_btn_{i}"):
                st.session_state[state_key] = d

    return st.session_state[state_key]


def plot_day_work_line(selected_date, color="#4FC3F7"):
    """
    Plots a line graph for the selected date.
    X-axis: hours 0..23
    Y-axis: 'working minutes' (demo series for now).
    """
    import numpy as np
    import matplotlib.pyplot as plt

    # ----- demo series (replace with real data later) -----
    hours = np.arange(24)
    # base: two peaks across the day; scale to minutes
    y = (np.sin((hours - 9) / 3.0) + 1.2).clip(min=0) * 20
    y += (np.sin((hours - 18) / 2.5) + 1.0).clip(min=0) * 25
    # small noise
    rng = np.random.default_rng(abs(hash(str(selected_date))) % (2**32))
    y = (y + rng.normal(0, 3, size=24)).clip(min=0)

    # ----- plot -----
    fig, ax = plt.subplots(figsize=(6.8, 2.3), facecolor="none")
    ax.set_facecolor("#0A0F18")
    ax.plot(hours, y, linewidth=2.2, color=color)
    ax.fill_between(hours, y, 0, color=color, alpha=0.18)

    ax.set_xlim(0, 23)
    ax.set_xticks([0, 6, 12, 18, 23])
    ax.set_xticklabels(["00", "06", "12", "18", "23"], color="#E6E6E6")
    ax.set_ylabel("Minutes", color="#E6E6E6")
    ax.set_xlabel("Time", color="#E6E6E6")

    ax.yaxis.grid(True, color="#263043", linewidth=0.6, alpha=0.7)
    for sp in ["top", "right", "left", "bottom"]:
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", colors="#9AA4B2")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
