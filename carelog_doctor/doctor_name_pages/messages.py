# doctor_name_pages/messages.py
from __future__ import annotations

from datetime import datetime
import streamlit as st

from doctor_name_services.messaging import (
    list_threads,
    get_thread,
    add_message,
    mark_resolved,
)

# ---------- version-safe rerun ----------
def _rerun():
    try:
        st.rerun()  # Streamlit >= 1.30
    except AttributeError:
        st.experimental_rerun()  # older Streamlit


def _ts(s: str):
    try:
        return datetime.fromisoformat(str(s).replace("Z", ""))
    except Exception:
        return None


def page_messages(store):
    st.markdown("### Secure Messaging")

    # ---------- shared page CSS (thread list + reply UI) ----------
    st.markdown(
        """
        <style>
        /* Thread list buttons */
        .threads .stButton>button{
            width:100%;
            text-align:left;
            background:#0D1422;
            color:#E6F4FF;
            border:1px solid rgba(148,163,184,0.28);
            border-radius:12px;
            padding:10px 12px;
            line-height:1.15;
        }
        .threads .stButton>button:hover{ background:#14213A; }
        .tiny{ font-size:12px; color:#9AA4B2; margin:2px 0 10px; }

        /* Reply textarea: dark bg, white text + placeholder */
        div[data-testid="stTextArea"] textarea {
            color: #EAF2FF !important;
            background: #0D1422 !important;
            border: 1px solid rgba(148,163,184,.35) !important;
            border-radius: 12px !important;
        }
        div[data-testid="stTextArea"] textarea::placeholder {
            color: #EAF2FF !important; opacity: .7 !important;
        }
        div[data-testid="stTextArea"] label p { color:#FFFFFF !important; }

        /* Styled submit buttons in the reply form */
        #reply-send button, #reply-resolve button {
            border-radius: 12px !important;
            padding: .6rem 1.1rem !important;
            border: 1px solid transparent !important;
            color: #FFFFFF !important;
            box-shadow: none !important;
        }
        /* Primary send */
        #reply-send button { background:#2E5AAC !important; }
        #reply-send button:hover { background:#3A6AD1 !important; }
        /* Resolve */
        #reply-resolve button { background:#B94141 !important; }
        #reply-resolve button:hover { background:#D45151 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---------- layout: 2 panes ----------
    left, right = st.columns([5, 7], gap="large")

    # ========== LEFT: thread list ==========
    with left:
        q = (
            st.text_input(
                "Search by patient or message…",
                key="msg_q",
                placeholder="Type to filter…",
            )
            or ""
        ).strip().lower()

        threads = list_threads(store) or []
        items = []
        for t in threads:
            msgs = t.get("messages") or []
            latest = msgs[-1] if msgs else {}
            name = t.get("name") or f"Patient #{t.get('patient_id','—')}"
            ts_raw = t.get("updated_at") or latest.get("timestamp")
            ts_dt = _ts(ts_raw)
            items.append(
                {
                    "id": t.get("id"),
                    "name": name,
                    "preview": (latest.get("text") or "").strip(),
                    "when_dt": ts_dt or datetime.min,
                    "when_str": ts_dt.strftime("%d/%m %H:%M") if ts_dt else "",
                    "status": t.get("status", "open"),
                }
            )

        items.sort(key=lambda r: r["when_dt"], reverse=True)

        if q:
            items = [
                r
                for r in items
                if (q in r["name"].lower() or q in r["preview"].lower())
            ]

        sel_key = "selected_thread_id"
        if sel_key not in st.session_state and items:
            st.session_state[sel_key] = items[0]["id"]

        st.markdown('<div class="threads">', unsafe_allow_html=True)
        for r in items:
            suffix = f" ({r['status']})" if r["status"] != "open" else ""
            label = f"{r['name']}{suffix}\n{r['preview']}"
            if st.button(label, key=f"open_thread_{r['id']}"):
                st.session_state[sel_key] = r["id"]
                _rerun()

            st.markdown(
                f"<div class='tiny'>{r['when_str']}</div>", unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ========== RIGHT: conversation ==========
    with right:
        tid = st.session_state.get("selected_thread_id")
        thr = get_thread(store, tid) if tid else None

        if not thr:
            st.info("Select a conversation on the left.")
            return

        st.markdown(
            f"**Thread #{thr.get('id')} • Patient #{thr.get('patient_id')} • Status: {thr.get('status','open')}**"
        )

        # chat bubbles
        for m in thr.get("messages", []):
            who = "Doctor" if (m.get("sender_role") == "doctor") else "Patient"
            ts = m.get("timestamp", "")
            align = "flex-end" if who == "Doctor" else "flex-start"
            bg = "#2E5AAC" if who == "Doctor" else "#0D1422"
            st.markdown(
                f"""
                <div style="display:flex; justify-content:{align}; margin:6px 0;">
                  <div style="max-width:80%; padding:10px 12px; border-radius:12px;
                              background:{bg}; border:1px solid rgba(255,255,255,0.10);">
                    <div style="font-size:12px; opacity:.8;">{who} • {ts}</div>
                    <div style="white-space:pre-wrap;">{m.get('text','')}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()

        # reply form
        with st.form(f"reply_form_{tid}", clear_on_submit=True):
            txt = st.text_area(
                "Reply", key=f"reply_text_{tid}", placeholder="Type your message…", height=100
            )
            c1, c2 = st.columns([3, 1])

            # Wrap buttons for CSS hooks
            with c1:
                st.markdown('<div id="reply-send">', unsafe_allow_html=True)
                send = st.form_submit_button("Send")
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown('<div id="reply-resolve">', unsafe_allow_html=True)
                resolve = st.form_submit_button("Mark Resolved")
                st.markdown("</div>", unsafe_allow_html=True)

        # handle actions
        if send and (txt or "").strip():
            add_message(store, tid, "doctor", (txt or "").strip())
            st.toast("Message sent", icon="✅")
            _rerun()

        if resolve and thr.get("status") != "resolved":
            mark_resolved(store, tid)
            st.toast("Thread marked resolved", icon="✅")
            _rerun()
