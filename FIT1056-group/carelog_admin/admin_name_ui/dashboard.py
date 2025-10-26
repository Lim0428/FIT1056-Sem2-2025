# admin_name_ui/dashboard.py
import streamlit as st
from datetime import datetime, date, timedelta
from collections import defaultdict
import pandas as pd
import altair as alt
# examples
from admin_name_utils.patients_io import list_patients, get_patient

from admin_name_utils.storage import load_db, save_db, external_admin_users
from admin_name_core.reporting import monthly_billing
from admin_name_utils.appointments_io import load_appointments

# 🔗 external data
from admin_name_utils.patients_io import list_patients, get_patient
from admin_name_utils.chat_io import load_chat, save_chat, append_message, unread_count_for_admin


# ---------- time helpers (LOCAL TIME AWARE) ----------
def _now_iso_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")

def _pretty_local(iso_str: str, with_date: bool = True) -> str:
    try:
        try:
            dt = datetime.fromisoformat(iso_str)
        except ValueError:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        local = dt.astimezone()
        return local.strftime("%Y-%m-%d %H:%M" if with_date else "%I:%M %p").lstrip("0")
    except Exception:
        return iso_str

def _format_time(iso: str):
    return _pretty_local(iso, with_date=False)

def _is_same_day(iso: str, d: date):
    try:
        try:
            dt = datetime.fromisoformat(iso)
        except ValueError:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().date() == d
    except Exception:
        return False


# ---------- generic UI helpers ----------
def _kpi_badge(label: str, value):
    st.markdown(
        f"""
        <div style="
            display:flex;align-items:center;justify-content:space-between;
            background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.10);
            border-radius:999px;padding:10px 16px;">
            <span style="opacity:.9">{label}</span>
            <span style="font-weight:700">{value}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _card_header(title: str, emoji: str = ""):
    st.markdown(
        f"""<div style='display:flex;align-items:center;gap:10px;'>
        <div style='font-size:20px'>{emoji}</div>
        <h4 style='margin:0;'>{title}</h4>
        </div>""",
        unsafe_allow_html=True,
    )

def _soft_card():
    return st.container(border=False)

def _appt_duration_hours(a: dict) -> float:
    """Compute duration in hours; fall back to 0.5h if end_iso missing/invalid."""
    try:
        try:
            start = datetime.fromisoformat(a["start_iso"])
        except ValueError:
            start = datetime.fromisoformat(a["start_iso"].replace("Z", "+00:00"))
        end_iso = a.get("end_iso")
        if not end_iso:
            return 0.5
        try:
            end = datetime.fromisoformat(end_iso)
        except ValueError:
            end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        dur = (end - start).total_seconds() / 3600.0
        if dur <= 0:
            return 0.5
        return min(dur, 8.0)
    except Exception:
        return 0.5

def _role_icon(role: str) -> str:
    role = (role or "").lower()
    if role == "admin":
        return "🛡️"
    if role == "doctor":
        return "🩺"
    if role == "nurse":
        return "🧑‍⚕️"
    if role == "psychological_counselor":
        return "🧠"
    if role == "staff":
        return "🧑‍💼"
    return "👤"

def _user_by_id(db, uid):
    return next((u for u in db.get("users", []) if u.get("id") == uid), None)

def _unique_patients_for_user(db, user):
    role = (user.get("role") or "").lower()
    if role in ("doctor", "nurse", "psychological_counselor"):
        pid_set = set(
            a.get("patient_id")
            for a in db.get("appointments", [])
            if a.get("patient_id") is not None and (
                (role == "doctor" and a.get("doctor_id") == user.get("id")) or
                (role == "nurse"  and a.get("nurse_id")  == user.get("id")) or
                (role == "psychological_counselor" and a.get("doctor_id") == user.get("id"))
            )
        )
        return len(pid_set)
    return len(list_patients())  # count from patient.json

def _upcoming_count_for_user(db, user, days=7):
    cutoff = date.today() + timedelta(days=days)
    role = (user.get("role") or "").lower()
    tally = 0
    for a in db.get("appointments", []):
        try:
            try:
                d = datetime.fromisoformat(a["start_iso"])
            except ValueError:
                d = datetime.fromisoformat(a["start_iso"].replace("Z", "+00:00"))
            d = d.astimezone().date()
        except Exception:
            continue
        if d < date.today() or d > cutoff:
            continue
        if role == "doctor" and a.get("doctor_id") != user.get("id"):
            continue
        if role == "nurse" and a.get("nurse_id") != user.get("id"):
            continue
        if role == "psychological_counselor" and a.get("doctor_id") != user.get("id"):
            continue
        tally += 1
    return tally

def _avg_rating_for_user(db, user):
    ratings = [r.get("score") for r in db.get("ratings", []) if r.get("user_id") == user.get("id")]
    if ratings:
        return round(sum(ratings) / len(ratings), 2)
    return 4.8

def _badge(text, tone="neutral"):
    tones = {
        "neutral": "rgba(255,255,255,.10)",
        "success": "rgba(34,197,94,.25)",
        "info":    "rgba(59,130,246,.25)",
        "warn":    "rgba(234,179,8,.25)"
    }
    return f"<span style='background:{tones.get(tone,'rgba(255,255,255,.10)')}; padding:4px 10px; border-radius:999px; font-size:12px;'>{text}</span>"

def _currency(n: float) -> str:
    return f"RM {n:,.2f}"


# ---------- Revenue helpers ----------
def _add_months(dt: date, months: int) -> date:
    y = dt.year + (dt.month - 1 + months) // 12
    m = (dt.month - 1 + months) % 12 + 1
    return date(y, m, 1)

def _month_key(dt: date) -> str:
    return dt.strftime("%Y-%m")

def _human_month(dt: date) -> str:
    return dt.strftime("%b %y")

def _build_month_df(bill_series: dict, start_month: date, end_month: date) -> pd.DataFrame:
    months = []
    cur = date(start_month.year, start_month.month, 1)
    end = date(end_month.year, end_month.month, 1)
    while cur <= end:
        mk = _month_key(cur)
        amt = float(bill_series.get(mk, 0.0))
        months.append({"MonthKey": mk, "Month": _human_month(cur), "Amount": amt, "Order": cur})
        cur = _add_months(cur, 1)
    df = pd.DataFrame(months)
    if df.empty:
        return df
    df = df.sort_values("Order")
    df["MoM_pct"] = df["Amount"].pct_change().fillna(0.0) * 100.0
    df["MA3"] = df["Amount"].rolling(3, min_periods=1).mean()
    df["is_zero"] = df["Amount"] == 0
    return df


# === role→chat file helpers ===
def _chat_role_of_user(u: dict) -> str:
    # decide which chat bucket this user belongs to
    r = (u.get("role") or "").lower()
    if r in ("doctor", "nurse", "psychological_counselor", "staff"):
        return r
    return "staff"

def _load_conv_for_peer(peer: dict) -> list[dict]:
    return load_chat(_chat_role_of_user(peer))

def _save_conv_for_peer(peer: dict, conv: list[dict]) -> None:
    save_chat(_chat_role_of_user(peer), conv)

def _append_msg_for_peer(peer: dict, message: dict) -> None:
    append_message(_chat_role_of_user(peer), message)


# ---------- page render ----------
def render():
    # --- after: db = load_db()
    db = load_db()
    user = st.session_state.get("user", {"name": "Admin", "role": "admin", "id": 0})

    # NEW: load appointments from data/appointments.json
    appts = load_appointments()

    # Title
    st.markdown(
        "<h3 style='display:flex;align-items:center;gap:10px;margin:0 0 6px 0;'>"
        "🏥 <span style='letter-spacing:.3px;'>Dashboard</span></h3>"
        "<p style='margin:0;opacity:.8;'>Real-time overview of operations</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # Patients from patient.json
    patients_json = list_patients()
    patients_count = len(patients_json)

    # KPI Row
    col1, col2, col3, col4 = st.columns(4)

    # staff from admin_users.json (exclude admins)
    ext_users = [u for u in (external_admin_users() or []) if (u.get("role","").lower() != "admin")]
    staff_count = len(ext_users)

    appts_today = sum(1 for a in appts if a.get("start_iso") and _is_same_day(a["start_iso"], date.today()))


    my_id = user.get("id")

    # unread across all role chats
    unread_msgs = unread_count_for_admin(my_id)

    with col1: _kpi_badge("Patients", patients_count)
    with col2: _kpi_badge("Staff", staff_count)
    with col3: _kpi_badge("Appointments Today", appts_today)
    with col4: _kpi_badge("Unread Messages", unread_msgs)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # === Middle row: Revenue • Today's Appointment • Your Profile ===
    colL, colM, colR = st.columns([1.5, 1.0, 1.0])

    # Revenue
    with colL:
        with _soft_card():
            _card_header("Revenue", "📈")
            st.caption("Monthly totals with a clean line chart. Tooltip shows RM and MoM %.")

            bill_series = monthly_billing(db)
            if not bill_series:
                st.info("No billing data yet.")
            else:
                # range selection
                col_r1, col_r2 = st.columns([1.2, 1])
                with col_r1:
                    range_opt = st.selectbox(
                        "Range", ["Last 6 months", "Last 12 months", "Year to date", "Custom year"], index=1
                    )
                with col_r2:
                    years = sorted({int(k.split("-")[0]) for k in bill_series.keys()}) or [date.today().year]
                    selected_year = st.selectbox("Year", years, index=len(years)-1, disabled=(range_opt != "Custom year"))

                today = date.today()
                if range_opt == "Last 6 months":
                    start = _add_months(date(today.year, today.month, 1), -5)
                    end = date(today.year, today.month, 1)
                elif range_opt == "Year to date":
                    start = date(today.year, 1, 1)
                    end = date(today.year, today.month, 1)
                elif range_opt == "Custom year":
                    start = date(selected_year, 1, 1)
                    end = date(selected_year, 12, 1)
                else:  # Last 12 months
                    start = _add_months(date(today.year, today.month, 1), -11)
                    end = date(today.year, today.month, 1)

                df = _build_month_df(bill_series, start, end)
                if df.empty:
                    st.info("No data for chosen range.")
                else:
                    # line chart (clean look)
                    line = alt.Chart(df).mark_line(point=True).encode(
                        x=alt.X("Month:N", sort=list(df["Month"]), title=None),
                        y=alt.Y("Amount:Q", title="RM"),
                        tooltip=[
                            alt.Tooltip("Month:N", title="Month"),
                            alt.Tooltip("Amount:Q", title="Revenue (RM)", format=",.2f"),
                            alt.Tooltip("MoM_pct:Q", title="MoM %", format=".1f"),
                        ],
                    )
                    st.altair_chart(line.properties(height=260), use_container_width=True)

                    csv = df[["MonthKey", "Month", "Amount", "MoM_pct", "MA3"]].copy()
                    csv.columns = ["month_key", "month_label", "amount_rm", "mom_pct", "ma3_rm"]
                    st.download_button(
                        "Download CSV",
                        data=csv.to_csv(index=False).encode("utf-8"),
                        file_name=f"revenue_{start.strftime('%Y%m')}_{end.strftime('%Y%m')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

    # Today's Appointments
    with colM:
        with _soft_card():
            _card_header("Today's Appointment", "🗓️")
            today = date.today()
            # Today's Appointment: replace the source list
#appointments", []) if a.get("status") == "booked" and _is_same_day(a["start_iso"], today)], key=lambda x: x["start_iso"])
            todays = sorted(
                [a for a in appts if (a.get("status") == "booked" and a.get("start_iso") and _is_same_day(a["start_iso"], today))],
                key=lambda x: x["start_iso"],
            )


            if not todays:
                st.info("No upcoming appointments.")
            else:
                for a in todays:
                    # patients are stored in patient.json (ids may be strings)
                    pid = a.get("patient_id")
                    patient = get_patient(str(pid)) or {"name": f"Patient #{pid}"}
                    # When checking earlier visits (the "First Visit" / "Consultation" tag):
# earlier = [x for x in db.get("appointments", []) if x.get("patient_id") == pid ...]
                    # When checking earlier visits (the "First Visit" / "Consultation" tag):
# earlier = [x for x in db.get("appointments", []) if x.get("patient_id") == pid ...]
                    earlier = [
                        x for x in appts
                        if x.get("patient_id") == pid
                        and x is not a
                        and x.get("start_iso")
                        and datetime.fromisoformat(x["start_iso"].replace("Z","+00:00")) <
                            datetime.fromisoformat(a["start_iso"].replace("Z","+00:00"))
                    ]


                    tag = "First Visit" if not earlier else "Consultation"
                    st.markdown(
                        f"""
                        <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:10px 12px;border:1px solid rgba(255,255,255,.08);
                            background:rgba(255,255,255,.03);border-radius:12px;margin-bottom:8px;">
                            <div style="display:flex;align-items:center;gap:10px;">
                              <div style="width:34px;height:34px;border-radius:999px;background:rgba(255,255,255,.08);
                                          display:flex;align-items:center;justify-content:center;">🧑‍⚕️</div>
                              <div>
                                <div style="font-weight:600;">{patient.get('name')}</div>
                                <div style="font-size:12px;opacity:.8;color:#9aa6bd;">{tag}</div>
                              </div>
                            </div>
                            <div style="opacity:.9">{_format_time(a["start_iso"])}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Your Profile
    with colR:
        with _soft_card():
            _card_header("Your Profile", "👤" if user.get("role") == "admin" else "🧑‍⚕️")
            me = _user_by_id(db, user.get("id")) or user
            role = (me.get("role") or "admin").title()
            email = me.get("email", "")
            spec  = me.get("specialization") or ("Operations" if role == "Admin" else "General")
            bio   = me.get("bio") or "No bio yet."
            icon  = _role_icon(me.get("role"))
            rating = _avg_rating_for_user(db, me)
            my_patients = _unique_patients_for_user(db, me)
            upcoming7 = _upcoming_count_for_user(db, me, days=7)

            st.markdown(
                f"""
                <div style="
                    border:1px solid rgba(255,255,255,.10);
                    border-radius:16px;padding:14px 14px 8px 14px; margin-bottom:10px;
                    background:linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,.02));
                ">
                  <div style="display:flex; align-items:center; gap:12px;">
                    <div style="width:54px;height:54px;border-radius:999px;
                          background:radial-gradient(60% 60% at 30% 30%, rgba(99,179,237,.9), rgba(59,130,246,.35));
                          display:flex;align-items:center;justify-content:center; font-size:26px;
                          box-shadow:0 0 0 2px rgba(255,255,255,.08) inset;">{icon}</div>
                    <div style="flex:1;">
                      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                        <div style="font-weight:800;font-size:18px">{me.get('name','User')}</div>
                        <div>{_badge(role, 'info')}</div>
                      </div>
                      <div style="opacity:.9; font-size:13px; margin-top:2px;">{email}</div>
                      <div style="opacity:.85; font-size:13px; margin-top:4px;">{spec}</div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            s1, s2, s3 = st.columns(3)
            with s1: st.metric("Overall Rating", f"{rating:.1f}")
            with s2: st.metric("Patients", f"{my_patients}")
            with s3: st.metric("Next 7d Appts", f"{upcoming7}")

            st.markdown(
                f"""
                <div style="margin-top:8px; border:1px solid rgba(255,255,255,.10);
                            border-radius:14px; padding:12px;">
                  <div style="font-weight:600; margin-bottom:6px;">About</div>
                  <div style="opacity:.9">{bio}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # === Bottom row: Duty Hour • Appointment History • Messages ===
    b1, b2, b3 = st.columns([1.2, 1.0, 1.2])

    # Duty Hour
    with b1:
        with _soft_card():
            _card_header("Duty Hour", "🕒")
            range_opt = st.radio("Range", ["Next 7 days", "Last 7 days"], horizontal=True, label_visibility="collapsed")
            base = date.today()
            forward = (range_opt == "Next 7 days")
            days = [base + timedelta(days=i) for i in (range(0,7) if forward else range(-6,1))]
            rows = []
            for d in days:
                # Duty Hour chart source:
# appts = [a for a in db.get("appointments", []) if _is_same_day(a["start_iso"], d) ...]
                day_appts = [
                    a for a in appts
                    if a.get("start_iso") and _is_same_day(a["start_iso"], d)
                    and (user.get("role") != "doctor" or a.get("doctor_id") == user.get("id"))
                ]
                total = sum(_appt_duration_hours(a) for a in day_appts)

                rows.append({"Day": d.strftime("%a %d"), "Hours": round(total, 2)})
            duty_df = pd.DataFrame(rows)
            area = alt.Chart(duty_df).mark_area(opacity=0.3).encode(
                x=alt.X('Day:N', sort=list(duty_df['Day']), title=None),
                y=alt.Y('Hours:Q', title='Hours')
            )
            line = alt.Chart(duty_df).mark_line(point=True).encode(
                x=alt.X('Day:N', sort=list(duty_df['Day']), title=None),
                y=alt.Y('Hours:Q', title='Hours'),
                tooltip=['Day:N', 'Hours:Q']
            )
            st.altair_chart((area + line).properties(height=220), use_container_width=True)
            st.caption("Duty Hour = sum of each appointment’s duration (end − start) per day. "
                       "If an appointment has no end time, it counts as 0.5h.")

    # Appointment History (this month)
    with b2:
        with _soft_card():
            _card_header("Appointment History", "📚")
            st.caption("Recap this month")
            start_month = date.today().replace(day=1)
            # Appointment History (this month):
# hist = [a for a in db.get("appointments", []) if ...]
            hist = [
                a for a in appts
                if a.get("start_iso")
                and datetime.fromisoformat(a["start_iso"].replace("Z","+00:00")).astimezone().date() >= start_month
                and (user.get("role") != "doctor" or a.get("doctor_id") == user.get("id"))
            ]

            if not hist:
                st.info("No appointments this month.")
            else:
                by_day = defaultdict(list)
                for a in hist:
                    d = datetime.fromisoformat(a["start_iso"].replace("Z","+00:00")).astimezone().date()
                    by_day[d].append(a)
                for d in sorted(by_day.keys(), reverse=True)[:3]:
                    st.markdown(f"**{d.strftime('%b %d')}**")
                    for a in sorted(by_day[d], key=lambda x: x["start_iso"]):
                        # lookup patient from patient.json
                        patient = get_patient(str(a.get("patient_id"))) or {"name": f"Patient #{a.get('patient_id','?')}"}
                        st.markdown(
                            f"- {_pretty_local(a['start_iso'])} · {patient['name']} · "
                            f"<span style='opacity:.8'>{a.get('status','').title()}</span>",
                            unsafe_allow_html=True,
                        )

    # Messages (role-based chat files + users from admin_users.json)
        # Messages (role-based chat files)
    with b3:
        with _soft_card():
            _card_header("Messages", "💬")

            # Load peers from data/admin_users.json (non-admin roles only)
            from admin_name_utils.users_io import load_admin_side_users
            peers_all = load_admin_side_users()

            # Filter out self (IDs may be str/int; compare as strings)
            my_id_str = str(my_id)
            others = [u for u in peers_all if str(u.get("id")) != my_id_str and not u.get("locked", False)]

            if not others:
                st.info("No users found in data/admin_users.json. Add doctors/nurses/staff/counselors there.")
                # Quick hint to the actual file path so we know we're reading the right place:
                try:
                    from admin_name_utils.users_io import admin_users_path
                    st.caption(f"Looking for: {admin_users_path()}")
                except Exception:
                    pass
                return

            names = [f"{u.get('name','User')} — {u.get('email','')} ({u.get('role','')})" for u in others]
            idx = st.selectbox("Chat with", list(range(len(names))), format_func=lambda i: names[i],
                               label_visibility="collapsed")
            peer = others[idx]
            peer_id = peer.get("id")

            # load the chat bucket for this peer's role
            full_msgs = _load_conv_for_peer(peer)

            # two-party slice (admin <-> selected user)
            conv = sorted(
                [m for m in full_msgs
                 if (str(m.get("from_id")) == my_id_str and str(m.get("to_id")) == str(peer_id))
                 or (str(m.get("from_id")) == str(peer_id) and str(m.get("to_id")) == my_id_str)],
                key=lambda m: m.get("ts","")
            )[-25:]

            # mark read & persist if necessary
            changed = False
            for m in full_msgs:
                if str(m.get("to_id")) == my_id_str and str(m.get("from_id")) == str(peer_id) and not m.get("read", False):
                    m["read"] = True
                    changed = True
            if changed:
                _save_conv_for_peer(peer, full_msgs)

            # bubbles
            bubble_css = """
            <style>
              .chat       { display:flex; flex-direction:column; gap:16px; padding:6px 2px; }
              .row        { display:flex; gap:12px; align-items:flex-end; }
              .row + .row { margin-top:10px; }
              .row.left   { justify-content:flex-start; }
              .row.right  { justify-content:flex-end;  }
              .avatar     {
                 width:32px; height:32px; border-radius:999px;
                 display:flex; align-items:center; justify-content:center;
                 background:rgba(255,255,255,.10);
                 box-shadow:inset 0 0 0 1px rgba(255,255,255,.14);
                 flex:0 0 32px; font-size:18px;
              }
              .bubble     { max-width:68vw; border-radius:18px; padding:12px 14px; line-height:1.28; }
              .me         { background:rgba(99,179,237,.28); border:1px solid rgba(99,179,237,.45); }
              .them       { background:rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.16); }
              .meta       { font-size:11px; opacity:.78; margin-top:6px; }
              @media (min-width: 1000px) { .bubble { max-width:42vw; } }
            </style>
            """
            st.markdown(bubble_css, unsafe_allow_html=True)
            st.markdown("<div class='chat'>", unsafe_allow_html=True)

            me_icon   = _role_icon(user.get("role"))
            them_icon = _role_icon(peer.get("role"))

            prev_from = None
            for m in conv:
                is_me = (str(m.get("from_id")) == my_id_str)
                klass = "right" if is_me else "left"
                bklass = "me" if is_me else "them"
                icon = me_icon if is_me else them_icon
                when = _pretty_local(m.get("ts", ""), with_date=True)
                top_margin = "18px" if prev_from is not None and prev_from != m.get("from_id") else "0"
                prev_from = m.get("from_id")

                if is_me:
                    html = (
                        f"<div class='row {klass}' style='margin-top:{top_margin};'>"
                        f"  <div class='bubble {bklass}'>"
                        f"    <div>{m.get('text','')}</div>"
                        f"    <div class='meta'>{when}</div>"
                        f"  </div>"
                        f"  <div class='avatar'>{icon}</div>"
                        f"</div>"
                    )
                else:
                    html = (
                        f"<div class='row {klass}' style='margin-top:{top_margin};'>"
                        f"  <div class='avatar'>{icon}</div>"
                        f"  <div class='bubble {bklass}'>"
                        f"    <div>{m.get('text','')}</div>"
                        f"    <div class='meta'>{when}</div>"
                        f"  </div>"
                        f"</div>"
                    )
                st.markdown(html, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            msg = st.text_input("Type a message and press Send", label_visibility="collapsed")
            send_col, sim_col = st.columns(2)
            with send_col:
                if st.button("Send", use_container_width=True, type="primary") and msg.strip():
                    _append_msg_for_peer(peer, {
                        "from_id": my_id,
                        "to_id": peer_id,
                        "text": msg.strip(),
                        "ts": _now_iso_local(),
                        "read": False,
                    })
                    st.rerun()
            with sim_col:
                if st.button("Simulate reply from selected user", use_container_width=True):
                    reply_text = f"Hi {user.get('name','there')}, this is {peer.get('name','User')} replying for test."
                    _append_msg_for_peer(peer, {
                        "from_id": peer_id,
                        "to_id": my_id,
                        "text": reply_text,
                        "ts": _now_iso_local(),
                        "read": False,
                    })
                    st.rerun()
