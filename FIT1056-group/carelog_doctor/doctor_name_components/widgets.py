# doctor_name_components/widgets.py
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter
import numpy as np
from datetime import datetime, timedelta

PRIMARY = "#2E5AAC"
ACCENT  = "#30C48D"
MUTED   = "#9AA4B2"

# ---------- Helpers ----------
def timestamp_label(dt_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(str(dt_iso).replace("Z",""))
        return dt.strftime("%d %b %Y • %H:%M")
    except Exception:
        return str(dt_iso) if dt_iso else "-"

def kpi_stat(label, value):
    st.markdown(
        f"""
        <div style="background: rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.10);
            border-radius: 999px;padding: 8px 14px;display:flex; align-items:center; justify-content:space-between;">
            <div style="font-size:12px;color:{MUTED};">{label}</div>
            <div style="font-size:22px;font-weight:800;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def revenue_chart(labels, values,
                  x_label="Revenue (RM)", y_label="Year",
                  bg_color="#0A1930", bar_color="#4FC3F7", grid=True):
    y_labels = list(labels)
    x_vals   = list(values)
    n = len(x_vals)
    text_color = "#FFFFFF"; grid_color = "#2A3750"
    fig, ax = plt.subplots(figsize=(7.2, 3.6), facecolor="none")
    ax.set_facecolor(bg_color)
    y_pos  = np.arange(n)[::-1]; height = 0.6; radius = height / 2
    for y, w in zip(y_pos, x_vals):
        ax.add_patch(FancyBboxPatch((0, y - height/2), w, height,
                     boxstyle=f"round,pad=0,rounding_size={radius}", linewidth=0, facecolor=bar_color))
    ax.set_ylim(-0.5, n - 0.5); ax.set_xlim(0, max(x_vals) * 1.1)
    ax.set_yticks(y_pos); ax.set_yticklabels(y_labels, color=text_color, fontsize=10)
    ax.set_xlabel(x_label, color=text_color, labelpad=8, fontsize=11, weight="bold")
    ax.set_ylabel(y_label, color=text_color, labelpad=8, fontsize=11, weight="bold")
    if grid: ax.xaxis.grid(True, color=grid_color, linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True); ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_: f"{int(x):,}"))
    for s in ["top", "right", "left", "bottom"]: ax.spines[s].set_visible(False)
    ax.tick_params(axis="x", colors=text_color, length=0, labelsize=9)
    ax.tick_params(axis="y", length=0, labelsize=9)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

# ---------- Cards & Lists ----------
def today_appointments_list(store):
    appts = store.list_upcoming_appointments(limit=5)
    rows = []
    if not appts:
        rows = [
            {"name":"Ucok Bendart","tag":"First Visit","time":"10:00 AM"},
            {"name":"Mac Jansen","tag":"Consultation","time":"12:00 PM"},
            {"name":"Anastasiya G","tag":"Consultation","time":"11:00 AM"},
            {"name":"Jimmi Jazz","tag":"First Visit","time":"1:00 PM"},
        ]
    else:
        for a in appts:
            t = a.get("start","")[11:16]
            if t:
                h,m = t.split(":"); hh=int(h); suffix="AM" if hh<12 else "PM"
                hh12 = hh if 1<=hh<=12 else (hh-12 if hh>12 else 12)
                tm = f"{hh12}:{m} {suffix}"
            else:
                tm = "-"
            rows.append({
                "name": a.get("patient_name") or f"Patient #{a.get('patient_id','—')}",
                "tag": a.get("reason","Consultation") or "Consultation",
                "time": tm
            })
    for r in rows:
        pressed = st.button(
            f"{r['name']} • {r['tag']} • {r['time']}",
            key=f"dash_appt_{r['name']}_{r['time']}",
            use_container_width=True
        )
        if pressed:
            st.session_state["nav"] = "Appointments"
            st.session_state["_route_push"] = True
            st.rerun()

def profile_card(store):
    name = store.doctor_display_name()
    avg, n = store.doctor_average_rating()
    total_patients = store.count_assigned_patients()
    st.markdown(
        f"""
        <div style="background: rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.10);
                    border-radius: 18px; padding: 14px;">
            <div style="font-weight:700;margin-bottom:6px;">Your Profile</div>
            <div style="display:flex; align-items:center; gap:12px;">
              <div style="width:56px;height:56px;border-radius:50%;background:#1f2937;display:flex;align-items:center;justify-content:center;font-size:26px;">🧑‍⚕️</div>
              <div>
                <div style="font-weight:700;">{name}</div>
                <div style="font-size:12px;color:{MUTED};">Doctor</div>
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

# ---------- Messages Panel (compact wrapper) ----------
def messages_panel(store):
    from doctor_name_services.messaging import list_threads
    threads = list_threads(store) or []
    if not threads:
        st.caption("No messages.")
        return
    for t in threads[:6]:
        last = (t.get("messages") or [{}])[-1]
        label = f"{t.get('name') or 'Patient'} • {last.get('text','')[:40]}"
        if st.button(label, key=f"dash_msg_{t.get('id')}"):
            st.session_state["selected_thread_id"] = t.get("id")
            st.session_state["nav"] = "Messages"
            st.session_state["_route_push"] = True
            st.rerun()

# ---------- Duty hour ----------
def duty_hour_strip_interactive(state_key="duty_selected"):
    from datetime import date
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]
    if state_key not in st.session_state:
        st.session_state[state_key] = today
    cols = st.columns(7)
    for i, c in enumerate(cols):
        d = days[i]; is_sel = (st.session_state[state_key] == d)
        label = d.strftime("%a %d")
        with c:
            if st.button(label, use_container_width=True, key=f"duty_btn_{i}"):
                st.session_state[state_key] = d
    return st.session_state[state_key]

def plot_day_work_line(selected_date, color="#4FC3F7"):
    hours = np.arange(24)
    y = (np.sin((hours - 9) / 3.0) + 1.2).clip(min=0) * 20
    y += (np.sin((hours - 18) / 2.5) + 1.0).clip(min=0) * 25
    rng = np.random.default_rng(abs(hash(str(selected_date))) % (2**32))
    y = (y + rng.normal(0, 3, size=24)).clip(min=0)
    fig, ax = plt.subplots(figsize=(6.8, 2.3), facecolor="none")
    ax.set_facecolor("#0A0F18")
    ax.plot(hours, y, linewidth=2.2, color=color)
    ax.fill_between(hours, y, 0, color=color, alpha=0.18)
    ax.set_xlim(0, 23); ax.set_xticks([0,6,12,18,23]); ax.set_xticklabels(["00","06","12","18","23"], color="#E6E6E6")
    ax.set_ylabel("Minutes", color="#E6E6E6"); ax.set_xlabel("Time", color="#E6E6E6")
    ax.yaxis.grid(True, color="#263043", linewidth=0.6, alpha=0.7)
    for sp in ["top","right","left","bottom"]: ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", colors="#9AA4B2")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

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

# ---------- Appointment History (dashboard widget) ----------
def appointment_history_list(store, month_only=True, limit=2, key_prefix="hist"):
    from datetime import datetime
    def _parse(s): 
        try: return datetime.fromisoformat(str(s).replace("Z",""))
        except: return None
    def _fmt(a):
        s=_parse(a.get("start","")); e=_parse(a.get("end",""))
        if not s: return "-"
        md=s.strftime("%b %d, %Y"); 
        def hm(d):
            h24,m=d.hour,d.minute; h12=12 if (h24%12)==0 else (h24%12); am="AM" if h24<12 else "PM"
            return f"{h12}:{m:02d} {am}"
        return f"{md} • {hm(s)}" + (f"–{hm(e)}" if e else "")
    now = datetime.now()
    rows = []
    for a in store.list_all_appointments():
        dt=_parse(a.get("start",""))
        if not dt or dt>=now: continue
        if month_only and not (dt.year==now.year and dt.month==now.month): continue
        rows.append(a)
    rows.sort(key=lambda x:_parse(x.get("start","")) or datetime.min, reverse=True)
    rows = rows[:limit]
    for i,a in enumerate(rows):
        title=(a.get("reason") or "Consultation").title()
        sub=_fmt(a)
        st.markdown(f"**{title}**"); st.caption(sub)
        if st.button("View", key=f"{key_prefix}_view_{a.get('id',i)}", use_container_width=True):
            st.session_state["selected_appt_id"] = a.get("id")
            st.session_state["nav"] = "Appointments"
            st.session_state["_route_push"] = True
            st.rerun()
