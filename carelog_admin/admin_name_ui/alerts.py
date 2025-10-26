# admin_name_ui/alerts.py
from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Set

from admin_name_utils.storage import load_db, save_db


# ---------- helpers ----------
def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _parse_iso(iso: str) -> datetime:
    return datetime.fromisoformat((iso or "").replace("Z", "+00:00"))

def _ensure_shapes(db: Dict[str, Any]) -> Dict[str, Any]:
    db.setdefault("alerts", [])
    db.setdefault("users", [])
    return db

def _by_id(users: List[Dict[str, Any]], uid: int | None) -> Dict[str, Any] | None:
    return next((u for u in users if u.get("id") == uid), None)

def _user_label(u: Dict[str, Any]) -> str:
    code = u.get("code") or f"#{u.get('id')}"
    name = u.get("name", "User")
    role = u.get("role", "")
    return f"{code} — {name} ({role})"

def _normalize_code(code: str) -> str:
    c = (code or "").strip().upper()
    if not c:
        return ""
    # Accept DSx as doctor too; normalize to DCx
    if c.startswith("DS"):
        return "DC" + c[2:]
    return c

def _users_by_codes(users: List[Dict[str, Any]], codes_text: str) -> tuple[List[Dict[str, Any]], List[str]]:
    target: Set[str] = set()
    for raw in (codes_text or "").replace(",", " ").split():
        norm = _normalize_code(raw)
        if norm:
            target.add(norm)
    if not target:
        return [], []

    index = {str(u.get("code") or "").upper(): u for u in users if u.get("code")}
    found, missing = [], []
    for c in sorted(target):
        (found if c in index else missing).append(index.get(c, c))  # type: ignore
    found = [x for x in found if isinstance(x, dict)]
    miss = [x for x in missing if isinstance(x, str)]
    return found, miss

def _next_alert_id(db: Dict[str, Any]) -> int:
    return max([a.get("id", 0) for a in db.get("alerts", [])] + [0]) + 1

def _status_pill(text: str, tone: str = "neutral") -> str:
    color = {
        "ok": "rgba(34,197,94,.25)",
        "warn": "rgba(250,204,21,.25)",
        "bad": "rgba(248,113,113,.25)",
        "neutral": "rgba(255,255,255,.12)",
        "info": "rgba(96,165,250,.25)",
    }.get(tone, "rgba(255,255,255,.12)")
    return (
        f"<span style='padding:3px 8px;border-radius:999px;"
        f"background:{color};border:1px solid rgba(255,255,255,.18);white-space:nowrap'>"
        f"{text}</span>"
    )


# ---------- page ----------
def render():
    db = _ensure_shapes(load_db())
    me = st.session_state.get("user", {"id": 0, "name": "Admin", "role": "admin"})
    my_id = int(me.get("id", 0))
    users: List[Dict[str, Any]] = db.get("users", [])

    st.markdown(
        "<h3 style='display:flex;align-items:center;gap:10px;margin:0 0 6px 0;'>"
        "🚨 <span>Alerts</span></h3>"
        "<p style='margin:0;opacity:.8;'>Send urgent notices to multiple team members by code (e.g. DS2, NS1) or by picking from the list. "
        "Recipients see them in their Inbox below.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ===== COMPOSE =====
    st.subheader("Send Alert")
    with st.container(border=True):
        colA, colB = st.columns([1, 1])
        with colA:
            pick_list = st.multiselect(
                "Select recipients",
                options=users,
                format_func=_user_label,
                placeholder="Pick doctors, nurses, staff…",
                key="alerts_pick_list",
            )
        with colB:
            codes_text = st.text_input(
                "Or enter codes (comma/space separated)",
                placeholder="e.g. DS2, NS1, ST3",
                key="alerts_codes",
            )
            via_codes, missing = _users_by_codes(users, codes_text)
            helper = []
            if via_codes:
                helper.append(_status_pill(f"Found {len(via_codes)} via codes", "ok"))
            if missing:
                helper.append(_status_pill(f"Unknown: {', '.join(missing)}", "bad"))
            if helper:
                st.markdown(" ".join(helper), unsafe_allow_html=True)

        # Merge list + codes, dedupe by id
        rmap = {u.get("id"): u for u in (pick_list or [])}
        for u in via_codes or []:
            rmap[u.get("id")] = u
        recipients = list(rmap.values())

        subject = st.text_input("Title (optional)", placeholder="Short title")
        body = st.text_area("Message", placeholder="Write your alert…", height=140)

        c1, c2 = st.columns([1, 1])
        with c1:
            priority = st.selectbox("Priority", ["Normal", "High", "Critical"], index=0)
        with c2:
            ack_required = st.checkbox("Require acknowledgment", value=False)

        if st.button(
            "Send",
            type="primary",
            use_container_width=True,
            disabled=(not recipients or not body.strip()),
        ):
            db = load_db()
            alerts: List[Dict[str, Any]] = db.get("alerts", [])
            alerts.append({
                "id": _next_alert_id(db),
                "from_id": my_id,
                "to_ids": [int(u.get("id")) for u in recipients],
                "subject": (subject or "").strip(),
                "body": body.strip(),
                "priority": priority.lower(),      # normal|high|critical
                "ack_required": bool(ack_required),
                "created_at": _now_iso(),
                "read_by": [],
                "acks": [],
            })
            db["alerts"] = alerts
            save_db(db)
            st.success(f"Alert sent to {len(recipients)} recipient(s).")
            for k in ("alerts_pick_list", "alerts_codes"):
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ===== INBOX =====
    st.subheader("Inbox")
    my_alerts = [a for a in db.get("alerts", []) if my_id in (a.get("to_ids") or [])]
    my_alerts = sorted(my_alerts, key=lambda a: a.get("created_at", ""), reverse=True)

    if not my_alerts:
        st.info("No alerts received.")
    else:
        f1, f2, f3 = st.columns([1, 1, 1])
        with f1:
            show_status = st.selectbox("Status", ["All", "Unread only", "Read only"], index=0)
        with f2:
            pr_filter = st.selectbox("Priority", ["All", "Normal", "High", "Critical"], index=0)
        with f3:
            text_search = st.text_input("Search title/body", placeholder="keywords…")

        def _include(a: Dict[str, Any]) -> bool:
            if pr_filter != "All" and a.get("priority", "normal").lower() != pr_filter.lower():
                return False
            if show_status == "Unread only" and my_id in (a.get("read_by") or []):
                return False
            if show_status == "Read only" and my_id not in (a.get("read_by") or []):
                return False
            if text_search:
                hay = (a.get("subject", "") + " " + a.get("body", "")).lower()
                if text_search.lower() not in hay:
                    return False
            return True

        inbox_list = [a for a in my_alerts if _include(a)]
        if not inbox_list:
            st.info("No alerts match the current filters.")
        else:
            for a in inbox_list[:30]:
                sender = _by_id(users, a.get("from_id"))
                subject = a.get("subject") or "(no title)"
                ts = _parse_iso(a.get("created_at", "")).strftime("%b %d, %H:%M")
                pr = (a.get("priority", "normal") or "normal").lower()
                pr_emoji = {"critical": "🔴", "high": "🟠", "normal": "⚪"}.get(pr, "⚪")
                read_txt = "Read" if my_id in (a.get("read_by") or []) else "Unread"
                ack_txt = " • ACK" if a.get("ack_required") else ""

                # Keep expander label plain text to avoid <span ...> showing
                expander_label = (
                    f"📨 {subject} • from {sender.get('name', 'User')} • {ts} • "
                    f"{pr_emoji} {pr.title()} • {read_txt}{ack_txt}"
                )

                with st.expander(expander_label, expanded=False):
                    # Pretty badges INSIDE the expander
                    badges = " ".join([
                        _status_pill(pr.title(), "bad" if pr == "critical" else ("warn" if pr == "high" else "neutral")),
                        _status_pill("ACK required", "info") if a.get("ack_required") else "",
                        _status_pill("Read", "ok") if my_id in (a.get("read_by") or []) else _status_pill("Unread", "info"),
                    ])
                    st.markdown(badges, unsafe_allow_html=True)

                    st.write(a.get("body", ""))
                    st.caption(f"From: {_user_label(sender)}  •  Sent: {ts}")

                    # Mark read on open
                    if my_id not in (a.get("read_by") or []):
                        a.setdefault("read_by", []).append(my_id)
                        save_db(db)  # persist immediately so badge updates

                    # Acknowledge if required
                    if a.get("ack_required"):
                        has_ack = my_id in (a.get("acks") or [])
                        if not has_ack and st.button("Acknowledge", key=f"ack_{a.get('id')}"):
                            a.setdefault("acks", []).append(my_id)
                            save_db(db); st.rerun()
                        elif has_ack:
                            st.success("You have acknowledged this alert.")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ===== SENT =====
    st.subheader("Sent")
    sent = [a for a in db.get("alerts", []) if a.get("from_id") == my_id]
    if not sent:
        st.caption("You haven't sent any alerts yet.")
        return

    rows = []
    for a in sorted(sent, key=lambda x: x.get("created_at", ""), reverse=True):
        total = len(a.get("to_ids") or [])
        read = len(a.get("read_by") or [])
        ack = len(a.get("acks") or [])
        rows.append({
            "When": _parse_iso(a.get("created_at", "")).strftime("%b %d %H:%M"),
            "Title": a.get("subject", "(no title)"),
            "Priority": (a.get("priority") or "normal").title(),
            "Recipients": total,
            "Read": f"{read}/{total}",
            "ACK": f"{ack}/{total}" if a.get("ack_required") else "—",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
