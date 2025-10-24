# doctor_name_pages/messages.py
from __future__ import annotations
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any


from doctor_name_services.messaging import (
    list_threads,
    get_thread,
    add_message,
    mark_resolved,
)

# ---------- helpers ----------
def _parse_ts(s: str) -> datetime:
    try:
        return datetime.fromisoformat(str(s).replace("Z", ""))
    except Exception:
        return datetime.min

def _pretty_time(s: str) -> str:
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", ""))
    except Exception:
        return ""
    today = datetime.now().date()
    if dt.date() == today:
        return dt.strftime("%H:%M")
    return dt.strftime("%d/%m/%Y")

def _bubble(sender: str, text: str, ts: str) -> None:
    me = (sender == "doctor")
    align = "flex-end" if me else "flex-start"
    bg    = "#2E5AAC" if me else "#0D1422"
    fg    = "#E6F0FF" if me else "#E2E8F0"
    meta  = f"{'Doctor' if me else 'Patient'} • {ts}"

    st.markdown(
        f"""
        <div style="display:flex; justify-content:{align}; margin:6px 0;">
          <div style="
              max-width:80%;
              background:{bg};
              color:{fg};
              border:1px solid rgba(255,255,255,0.10);
              border-radius:14px;
              padding:10px 12px;">
            <div style="font-size:11px; opacity:.8; margin-bottom:4px;">{meta}</div>
            <div style="white-space:pre-wrap; line-height:1.35">{text}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- page ----------
def page_messages(store):
    st.markdown("### Secure Messaging")

    # CSS: Messenger-like list + tidy inputs
    st.markdown(
    """
    <style>
    /* Messenger-like thread buttons */
    .threads-wrap .stButton > button {
        width: 100%;
        justify-content: flex-start;
        background: #0D1422;
        border: 1px solid rgba(148,163,184,0.28);
        color: #E5E7EB;
        padding: 12px 14px;
        border-radius: 12px;
        white-space: pre-line;          /* allow \\n in labels to show as new lines */
        text-align: left;
        line-height: 1.15;
        font-weight: 600;
    }
    .threads-wrap .stButton > button:hover {
        background: #121B2C;
        border-color: rgba(148,163,184,0.40);
    }
    .threads-wrap .stButton > button:focus {
        outline: none;
        box-shadow: 0 0 0 3px rgba(79,195,247,0.15) inset;
    }
    /* Dim the “secondary” lines (preview + time) by placing them after a \\n in label */
    .threads-wrap .stButton > button {
        /* we can’t target lines separately, so we simulate with lighter color in text */
    }
    .pane {
        background: rgba(255,255,255,0.04);
        border:1px solid rgba(148,163,184,0.25);
        border-radius:14px;
        padding:12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


    # --- read threads + normalize ---
    raw_threads: List[Dict[str, Any]] = list_threads(store) or []
    items = []
    for t in raw_threads:
        msgs = t.get("messages") or []
        latest = msgs[-1] if msgs else {}
        items.append({
            "id": t.get("id"),
            "patient_id": t.get("patient_id"),
            "name": t.get("name") or f"Patient #{t.get('patient_id','—')}",
            "status": t.get("status", "open"),
            "preview": (latest.get("text") or "").strip(),
            "updated_at": t.get("updated_at") or latest.get("timestamp") or "",
        })
    # newest first
    items.sort(key=lambda r: _parse_ts(r["updated_at"]), reverse=True)

    # --- left/right layout ---
    left, right = st.columns([4, 8], gap="large")

    # -------- LEFT: Messenger-like thread list --------
    with left:
        with st.container(border=True):
            st.markdown("**Threads**")
            q = st.text_input("Search", placeholder="Search by patient or message…", label_visibility="collapsed")
            ql = (q or "").strip().lower()

            filtered = [r for r in items if (ql in r["name"].lower() or ql in r["preview"].lower())] if ql else items

            # ensure a selected thread id in session (default to first in filtered/newest)
            sel_key = "messages_selected_thread"
            if sel_key not in st.session_state and filtered:
                st.session_state[sel_key] = filtered[0]["id"]

            # Render as a vertical list of “rows”
            st.markdown('<div class="threads-wrap">', unsafe_allow_html=True)
            for r in filtered:
                status_icon = "●" if r["status"] == "open" else "○"
                name_line   = f"{status_icon} {r['name']}"
                preview     = (r['preview'] or "—").strip().replace("\n", " ")
                preview     = preview if len(preview) <= 70 else preview[:67] + "…"
                time_line   = _pretty_time(r["updated_at"])
                # Use \\n to create two soft lines under the title
                label = f"{name_line}\n{preview}\n{time_line}"

                if st.button(label, key=f"open_{r['id']}"):
                    st.session_state[sel_key] = r["id"]
            st.markdown('</div>', unsafe_allow_html=True)

                        

    # -------- RIGHT: Conversation + actions --------
    with right:
        # resolve the selected id to a thread
        tid = st.session_state.get("messages_selected_thread")
        thr = get_thread(store, tid) if tid else None

        if not thr:
            st.info("Select a thread from the left to view messages.")
            return

        with st.container(border=True):
            st.markdown(
                f"**{thr.get('name') or f'Patient #{thr.get('patient_id','—')}'}**  \n"
                f"<span class='muted'>Thread #{thr.get('id')} • Status: {thr.get('status','open')}</span>",
                unsafe_allow_html=True,
            )

            # history (oldest -> newest)
            for m in thr.get("messages", []):
                _bubble(
                    sender=m.get("sender_role", "patient"),
                    text=m.get("text", ""),
                    ts=_pretty_time(m.get("timestamp", "")),
                )

            st.divider()

            # Actions OUTSIDE the form
            c1, c2 = st.columns([1, 1])
            with c1:
                # keep manual resolve too
                if st.button("Mark Resolved", use_container_width=True, key=f"resolve_{thr['id']}"):
                    if thr.get("status") != "resolved":
                        mark_resolved(store, thr["id"])
                        st.success("Thread marked resolved.")
                        st.rerun()
                    else:
                        st.info("Already resolved.")
            with c2:
                if st.button("Simulate Patient Reply (demo)", use_container_width=True, key=f"sim_{thr['id']}"):
                    add_message(store, thr["id"], "patient", "Thanks doctor, noted.")
                    st.info("Simulated patient reply added.")
                    st.rerun()

            with st.form(key=f"reply_form_{thr['id']}", clear_on_submit=True):
                msg = st.text_area("Reply", placeholder="Type your message…", height=110)
                sent = st.form_submit_button("Send", use_container_width=True)
                if sent:
                    if msg.strip():
                        ok = add_message(store, thr["id"], "doctor", msg.strip())
                        # Auto-resolve the thread right after sending
                        mark_resolved(store, thr["id"])
                        if ok:
                            st.success("Message sent and thread marked resolved.")
                            st.rerun()
                        else:
                            st.error("Failed to send. Check thread ownership / JSON file.")
                    else:
                        st.warning("Message is empty.")

            
