# doctor_name_components/widgets.py
# -------------------------------------------------------------------
# Shared UI widgets for the Doctor dashboard
# -------------------------------------------------------------------
import streamlit as st
from datetime import datetime, timedelta

PRIMARY = "#2E5AAC"
ACCENT  = "#30C48D"
MUTED   = "#9AA4B2"

# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------
def timestamp_label(dt_iso: str) -> str:
    """Format ISO like '2025-10-23T10:30:00' -> '23 Oct 2025 • 10:30'."""
    try:
        dt = datetime.fromisoformat(str(dt_iso).replace("Z", ""))
        return dt.strftime("%d %b %Y • %H:%M")
    except Exception:
        return str(dt_iso) if dt_iso else "-"

# -------------------------------------------------------------------
# KPI chip
# -------------------------------------------------------------------
def kpi_stat(label: str, value):
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

# -------------------------------------------------------------------
# Revenue chart (horizontal rounded bars): dark blue bg, light blue bars, white text
# -------------------------------------------------------------------
def revenue_chart(labels, values,
                  x_label="Revenue (RM)", y_label="Year",
                  bg_color="#0A1930", bar_color="#4FC3F7", grid=True):
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    from matplotlib.ticker import FuncFormatter
    import numpy as np

    y_labels = list(labels)
    x_vals   = list(values)
    n = len(x_vals)

    text_color = "#FFFFFF"
    grid_color = "#2A3750"

    fig, ax = plt.subplots(figsize=(7.2, 3.6), facecolor="none")
    ax.set_facecolor(bg_color)

    # positions (reverse so first label is at top)
    y_pos  = np.arange(n)[::-1]
    height = 0.6
    radius = height / 2

    # draw rounded bars
    for y, w in zip(y_pos, x_vals):
        ax.add_patch(FancyBboxPatch(
            (0, y - height/2), w, height,
            boxstyle=f"round,pad=0,rounding_size={radius}",
            linewidth=0,
            facecolor=bar_color
        ))

    # padding so top/bottom bars aren't clipped
    ax.set_ylim(-0.5, n - 0.5)
    ax.set_xlim(0, max(x_vals) * 1.1)

    # ticks/labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels, color=text_color, fontsize=10)
    ax.set_xlabel(x_label, color=text_color, labelpad=8, fontsize=11, weight="bold")
    ax.set_ylabel(y_label, color=text_color, labelpad=8, fontsize=11, weight="bold")

    if grid:
        ax.xaxis.grid(True, color=grid_color, linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _ : f"{int(x):,}"))

    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="x", colors=text_color, length=0, labelsize=9)
    ax.tick_params(axis="y", length=0, labelsize=9)

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

# -------------------------------------------------------------------
# Today's appointments (compact list)
def today_appointments_list(store):
    """
    Renders ONLY today's appointments from JSON. Each row is clickable and
    sends the user to the Appointments page with that appointment selected.
    """
    from datetime import datetime

    # 1) Pull from JSON and filter to "today"
    today = datetime.now().date()

    # Try common store methods without assuming one exists
    appts = []
    if hasattr(store, "list_all_appointments"):
        appts = store.list_all_appointments() or []
    elif hasattr(store, "list_upcoming_appointments"):
        appts = store.list_upcoming_appointments(limit=5000) or []
    else:
        appts = []  # nothing else we can do

    def _is_today(iso: str) -> bool:
        try:
            d = datetime.fromisoformat(iso.replace("Z", "")).date()
            return d == today
        except Exception:
            return False

    todays = [a for a in appts if _is_today(a.get("start", ""))]

    # Sort by start time
    def _key(a):
        try:
            return datetime.fromisoformat(a["start"].replace("Z",""))
        except Exception:
            return datetime.max
    todays.sort(key=_key)

    if not todays:
        st.info("No appointments scheduled for today.")
        return

    # 2) Render as clickable rows (neutral style)
    for a in todays:
        # Patient display name
        pname = a.get("patient_name") or f"Patient #{a.get('patient_id','—')}"
        tag   = a.get("reason", "Consultation") or "Consultation"

        # Time: 24h -> AM/PM
        try:
            dt  = datetime.fromisoformat(a["start"].replace("Z",""))
            hh  = dt.hour
            mm  = dt.minute
            suf = "AM" if hh < 12 else "PM"
            hh12 = hh if 1 <= hh <= 12 else (hh-12 if hh>12 else 12)
            time_label = f"{hh12}:{mm:02d} {suf}"
        except Exception:
            time_label = a.get("start","")

        # One full-width button per appointment
        pressed = st.button(
            f"{pname}\n{tag} • {time_label}",
            key=f"appt_row_{a.get('id',id(a))}",
            use_container_width=True,
            type="secondary",
        )
        st.markdown("<div style='border-bottom:1px solid rgba(255,255,255,0.08);'></div>", unsafe_allow_html=True)

        if pressed:
            st.session_state["selected_appt_id"] = a.get("id")
            st.session_state["nav"] = "Appointments"   # Title-case
            st.session_state["_route_push"] = True     # <- tell app.py to honor this once
            st.rerun()


# -------------------------------------------------------------------
# Profile card
# -------------------------------------------------------------------
def profile_card(store):
    name = store.doctor_display_name()
    role = getattr(st.session_state, "auth", {}).get("user", {}).get("specialty", "Doctor")
    avg, n = store.doctor_average_rating()
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

# -------------------------------------------------------------------
# Interactive Messages panel (click to open, send with chat_input)
# -------------------------------------------------------------------
def messages_panel(store):
    """
    Neutral message panel with full-thread search:
      • Case-insensitive search across thread name + ALL messages (doctor & patient)
      • Click a row to open conversation (secondary buttons)
      • Dark neutral chat bubbles
      • Send via st.chat_input
      • Oldest -> newest so newest shows at the bottom
    """
    import streamlit as st
    from datetime import datetime
    from doctor_name_services.messaging import list_threads, get_thread, add_message, mark_resolved

    def _parse_ts(s: str):
        try:
            return datetime.fromisoformat(str(s).replace("Z", ""))
        except Exception:
            return datetime.min

    # --- search box ---
    query = (st.text_input(
        "Search for chats",
        key="dash_msg_query",
        label_visibility="collapsed",
        placeholder="Search for chats",
    ) or "").strip().lower()

    # '+' button (neutral)
    cols = st.columns([1, 0.12])
    with cols[1]:
        st.button("+", use_container_width=True, key="dash_msg_new_btn", type="secondary")

    # --- load threads ---
    threads = list_threads(store) or []

    # Build render items + a FULL-TEXT field (all messages, doctor + patient)
    items = []
    for t in threads:
        msgs = t.get("messages") or []
        latest = msgs[-1] if msgs else {}
        preview = str(latest.get("text", "")).strip()
        name = t.get("name") or f"Patient #{t.get('patient_id','—')}"
        when = t.get("updated_at") or latest.get("timestamp") or ""

        # 🔎 index text = thread name + all message texts (doctor & patient)
        all_text = " ".join([m.get("text", "") for m in msgs])
        search_blob = f"{name} {all_text}".lower()

        items.append({
            "id": t.get("id"),
            "name": name,
            "preview": preview,
            "when": when,
            "search_blob": search_blob,
        })

    # Case-insensitive filter across full thread text
    if query:
        items = [r for r in items if query in r["search_blob"]]

    # Sort oldest -> newest so newest shows at the bottom
    items.sort(key=lambda r: _parse_ts(r["when"]))

    # Selection (default to newest)
    sel_key = "dash_selected_thread"
    valid_ids = {r["id"] for r in items}
    if items and st.session_state.get(sel_key) not in valid_ids:
        st.session_state[sel_key] = items[-1]["id"]

    # --- clickable rows (neutral buttons) ---
    for r in items:
        dt = _parse_ts(r["when"])
        when_str = dt.strftime("%H:%M") if dt.date() == datetime.now().date() else dt.strftime("%d/%m/%Y")
        if st.button(f"{r['name']} • {when_str}\n{r['preview']}",
                     key=f"open_{r['id']}",
                     use_container_width=True,
                     type="secondary"):
            st.session_state[sel_key] = r["id"]

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # --- conversation view ---
    tid = st.session_state.get(sel_key)
    if not tid:
        if not items:
            st.info("No conversations yet.")
        return

    thr = get_thread(store, tid)
    if not thr:
        st.warning("Thread not found or not permitted.")
        return

    st.markdown(f"**Thread #{thr['id']}** • Patient #{thr['patient_id']} • Status: {thr.get('status','open')}")

    # History (oldest -> newest) with neutral bubbles
    for m in thr.get("messages", []):
        mine = (m.get("sender_role") == "doctor")
        align = "flex-end" if mine else "flex-start"
        bg    = "#1f2937" if mine else "#0D1422"
        st.markdown(
            f"""
            <div style="display:flex; justify-content:{align}; margin:4px 0;">
              <div style="max-width:80%; padding:8px 12px; border-radius:12px;
                          background:{bg}; border:1px solid rgba(255,255,255,0.10);">
                <div style="font-size:12px; opacity:.8;">{'Doctor' if mine else 'Patient'} • {m.get('timestamp','')}</div>
                <div style="white-space:pre-wrap;">{m.get('text','')}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Actions (neutral)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Mark Resolved", use_container_width=True, type="secondary") and thr.get("status") != "resolved":
            mark_resolved(store, tid)
            st.success("Thread marked resolved.")
            st.rerun()
    with c2:
        if st.button("Simulate Patient Reply (demo)", use_container_width=True, type="secondary"):
            add_message(store, tid, "patient", "Thanks doctor, noted.")
            st.info("Simulated patient reply added.")
            st.rerun()

    # Reply input
    reply = st.chat_input("Type your message…")
    if reply:
        if add_message(store, tid, "doctor", reply.strip()):
            st.rerun()
        else:
            st.error("Failed to send. Check thread ownership/JSON permissions.")


# -------------------------------------------------------------------
# Duty hour: simple HTML strip (non-interactive)
# -------------------------------------------------------------------
def duty_hour_strip():
    from streamlit.components.v1 import html
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
          <div style="border-radius:12px; padding:10px; text-align:center;
                      background:{bg}; color:{txt}; border:1px solid {bord};">
            <div style="font-size:11px;color:#9AA4B2;">{d.strftime('%a')}</div>
            <div style="font-weight:700;">{d.strftime('%d')}</div>
          </div>
        """)
    html(f"<div style='display:grid; grid-template-columns:repeat(7,1fr); gap:10px;'>{''.join(cards)}</div>",
         height=110, scrolling=False)

# -------------------------------------------------------------------
# Duty hour: interactive 7-day strip + per-day line chart
def duty_hour_strip_interactive(state_key="duty_selected"):
    """
    7 compact chips (Mon..Sun). Selected chip is clearer (higher-contrast
    wrapper and subtle shadow). Single-click selection.
    """
    from datetime import datetime, timedelta

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    if state_key not in st.session_state:
        st.session_state[state_key] = today

    def _select_day(d):
        st.session_state[state_key] = d  # single-click update

    cols = st.columns(7)
    for i, col in enumerate(cols):
        d = days[i]
        is_sel = (st.session_state[state_key] == d)
        label = f"{d.strftime('%a')} {d.day}" + ("  ●" if is_sel else "")

        with col:
            if is_sel:
                # Brighter, clearer wrapper (higher-contrast border & bg)
                st.markdown(
                    """
                    <div style="
                        padding:8px;
                        border-radius:16px;
                        background:rgba(148,163,184,0.10);   /* slate-400 @10% */
                        border:1px solid rgba(148,163,184,0.35);
                        box-shadow: 0 1px 6px rgba(0,0,0,0.25);
                    ">
                    """,
                    unsafe_allow_html=True,
                )

            st.button(
                label,
                key=f"duty_btn_{i}",
                use_container_width=True,
                type="secondary",
                on_click=_select_day,
                args=(d,),
            )

            if is_sel:
                st.markdown("</div>", unsafe_allow_html=True)

    return st.session_state[state_key]



def plot_day_work_line(selected_date, color="#4FC3F7"):
    """Line graph with time (x) and minutes (y) for the selected day."""
    import numpy as np
    import matplotlib.pyplot as plt

    hours = np.arange(24)
    # Demo shape: morning & evening peaks; deterministic noise by date hash
    y = (np.sin((hours - 9) / 3.0) + 1.2).clip(min=0) * 20
    y += (np.sin((hours - 18) / 2.5) + 1.0).clip(min=0) * 25
    rng = np.random.default_rng(abs(hash(str(selected_date))) % (2**32))
    y = (y + rng.normal(0, 3, size=24)).clip(min=0)

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
    ax.tick_params(axis="y", colors=MUTED)

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

# -------------------------------------------------------------------
# Appointment history + overall appointment mini card
# -------------------------------------------------------------------
def appointment_history_list(store, month_only: bool = True, limit: int | None = None):
    """
    Past appointments list with clearer contrast. 'View' opens the detail page.
    """
    from datetime import datetime

    appts = store.list_all_appointments() or []
    now = datetime.now()

    def _parse(iso: str):
        try:
            return datetime.fromisoformat(str(iso).replace("Z", ""))
        except Exception:
            return None

    # OS-safe time formatter (no %-I for Windows)
    def _hm(dt: datetime, include_ampm: bool = True) -> str:
        h24, m = dt.hour, dt.minute
        h12 = 12 if (h24 % 12) == 0 else (h24 % 12)
        ampm = "AM" if h24 < 12 else "PM"
        core = f"{h12}" if m == 0 else f"{h12}:{m:02d}"
        return f"{core} {ampm}" if include_ampm else core

    def _fmt_range(a: dict) -> str:
        s = _parse(a.get("start", ""))
        e = _parse(a.get("end", ""))
        if not s: return "-"
        md = s.strftime("%b %d")
        if e:
            same_ampm = ("AM" if s.hour < 12 else "PM") == ("AM" if e.hour < 12 else "PM")
            if same_ampm:
                return f"{md} • {_hm(s, include_ampm=False)}–{_hm(e)}"
            return f"{md} • {_hm(s)}–{_hm(e)}"
        return f"{md} • {_hm(s)}"

    # filter: past (optionally only this month)
    past = []
    for a in appts:
        dt = _parse(a.get("start", ""))
        if dt and dt < now and (not month_only or (dt.year == now.year and dt.month == now.month)):
            past.append(a)

    past.sort(key=lambda x: _parse(x.get("start", "")) or datetime.min, reverse=True)
    if limit:
        past = past[:limit]

    if not past:
        st.info("No appointment history to show.")
        return

    for a in past:
        title = a.get("reason", "Consultation") or "Consultation"
        subtitle = _fmt_range(a)

        # Higher-contrast row: brighter title, clearer subtitle, stronger divider
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:12px; padding:12px;
                        border-bottom:1px solid rgba(148,163,184,0.30);">
              <div style="width:38px;height:38px;border-radius:10px;
                          background:#0B1220;
                          border:1px solid rgba(148,163,184,0.35);
                          display:flex;align-items:center;justify-content:center;">📌</div>
              <div style="flex:1 1 auto; min-width:0;">
                <div style="font-weight:700; color:#E5E7EB;">{title}</div>
                <div style="font-size:12px; color:#CBD5E1; margin-top:2px;">{subtitle}</div>
              </div>
              <div style="margin-left:auto;">
            """,
            unsafe_allow_html=True
        )

        # 'View' button: still secondary, but with a higher-contrast outline
        # (Streamlit controls button colors; we enhance contrast via the container above.)
        view = st.button(
            "View",
            key=f"hist_view_{a.get('id', id(a))}",
            type="secondary",
        )

        st.markdown("</div></div>", unsafe_allow_html=True)

        if view:
            st.session_state["selected_appt_id"] = a.get("id")
            st.session_state["nav"] = "Appointments"
            st.session_state["_route_push"] = True
            st.rerun()



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
