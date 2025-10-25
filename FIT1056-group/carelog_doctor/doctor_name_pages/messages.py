# doctor_name_pages/messages.py
import streamlit as st
from datetime import datetime
from doctor_name_services.messaging import list_threads, get_thread, add_message, mark_resolved

def _parse_ts(s: str):
    try: return datetime.fromisoformat(str(s).replace("Z",""))
    except: return datetime.min

def _row_html(name, preview, when, status):
    dot = "resolved" if status == "resolved" else "open"
    return f"""
    <div class="thread-row">
      <div class="thread-avatar">💬</div>
      <div class="thread-body">
        <div class="thread-name"><span class="status-dot {dot}"></span>{name}</div>
        <div class="thread-preview">{preview}</div>
      </div>
      <div class="thread-right">{when}</div>
    </div>
    """

def page_messages(store):
    st.markdown("### Secure Messaging")

    st.markdown(
        """
        <style>
        .thread-row { display:flex; align-items:center; gap:10px; padding:10px; border:1px solid rgba(148,163,184,0.25);
          border-radius:12px; background:#0B1220; }
        .thread-row + .thread-row { margin-top:8px; }
        .thread-avatar { width:34px;height:34px;border-radius:50%; background:#0E1626; display:flex; align-items:center; justify-content:center;
          border:1px solid rgba(148,163,184,0.35); }
        .thread-name { font-weight:700; color:#E6F0FF; }
        .thread-preview { color:#94A3B8; font-size:12px; }
        .thread-right { color:#9AA6B2; font-size:12px; margin-left:auto; }
        .status-dot { width:8px;height:8px;border-radius:999px;display:inline-block;margin-right:6px; }
        .status-dot.open { background:#35c78a; }
        .status-dot.resolved { background:#64748b; }
        </style>
        """, unsafe_allow_html=True)

    q = (st.text_input("Search by patient or message…", key="msg_q", label_visibility="collapsed") or "").lower().strip()
    threads = list_threads(store) or []
    items = []
    for t in threads:
        msgs = t.get("messages") or []
        latest = msgs[-1] if msgs else {}
        preview = str(latest.get("text", "")).strip()
        name = t.get("name") or f"Patient #{t.get('patient_id','—')}"
        when = t.get("updated_at") or latest.get("timestamp") or ""
        items.append({"id": t.get("id"), "name": name, "preview": preview, "when": when, "status": t.get("status","open")})
    if q:
        items = [r for r in items if q in r["name"].lower() or q in r["preview"].lower()]
    items.sort(key=lambda r: _parse_ts(r["when"]), reverse=True)

    left, right = st.columns([5,7], gap="large")
    with left:
        st.markdown("**Threads**")
        for r in items:
            dt = _parse_ts(r["when"])
            when_str = dt.strftime("%H:%M") if dt.date() == datetime.now().date() else dt.strftime("%d/%m/%Y")
            html = _row_html(r["name"], r["preview"], when_str, r["status"])
            if st.button(html, key=f"open_{r['id']}", use_container_width=True):
                st.session_state["selected_thread_id"] = r["id"]
                st.rerun()

    with right:
        tid = st.session_state.get("selected_thread_id") or (items[0]["id"] if items else None)
        if not tid:
            st.info("Select a thread."); return
        thr = get_thread(store, tid)
        if not thr:
            st.warning("Thread not found."); return

        st.markdown(f"**Thread #{thr['id']} • Patient #{thr['patient_id']} • Status: {thr.get('status','open')}**")
        for m in thr.get("messages", []):
            who = "Doctor" if m.get("sender_role") == "doctor" else "Patient"
            align = "flex-end" if who == "Doctor" else "flex-start"
            bg    = "#2E5AAC" if who == "Doctor" else "#0D1422"
            st.markdown(
                f"""
                <div style="display:flex; justify-content:{align}; margin:4px 0;">
                  <div style="max-width:80%; padding:8px 12px; border-radius:12px;
                              background:{bg}; border:1px solid rgba(255,255,255,0.10);">
                    <div style="font-size:12px; opacity:.8;">{who} • {m.get('timestamp','')}</div>
                    <div style="white-space:pre-wrap;">{m.get('text','')}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with st.form(f"send_form_{tid}", clear_on_submit=True):
            txt = st.text_area("Reply", placeholder="Type your message…", height=100)
            c1, c2 = st.columns([1,1])
            send = c1.form_submit_button("Send", use_container_width=True)
            resolve = c2.form_submit_button("Mark Resolved", use_container_width=True)

            if send and txt.strip():
                add_message(store, tid, "doctor", txt.strip())
                mark_resolved(store, tid)  # auto-resolve
                st.success("Sent & marked resolved.")
                st.rerun()

            if resolve and thr.get("status") != "resolved":
                mark_resolved(store, tid)
                st.success("Thread marked resolved.")
                st.rerun()
