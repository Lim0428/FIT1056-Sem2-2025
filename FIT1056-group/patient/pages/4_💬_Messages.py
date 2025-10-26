# pages/4_💬_Messages.py
from __future__ import annotations
import io, base64
from pathlib import Path
from datetime import datetime, timedelta
import streamlit as st

from components.ui import apply_theme, page_header, card, require_auth
from app.messaging import MessagingService
from app.patient import PatientService

# ---------------- Boot & theme ----------------
st.set_page_config(page_title="Messages", page_icon="💬", layout="wide")
apply_theme()
require_auth()
page_header("Messages", "Chat with your care team", "💬")

svc = MessagingService()
psvc = PatientService()
pid = st.session_state["auth_user"]
profile = psvc.get(pid) or {}

# ---------------- Avatars ----------------
PAGES_DIR = Path(__file__).resolve().parent  # .../patient/pages
REPO_ROOT = PAGES_DIR.parent                 # .../FIT1056-GROUP
def _read_avatar_b64(rel_path: str | None) -> str | None:
    if not rel_path:
        return None
    try:
        full = (REPO_ROOT / rel_path).resolve()
        data = full.read_bytes()
        return base64.b64encode(data).decode("utf-8")
    except Exception:
        return None

patient_avatar_rel = profile.get("avatar_path")  # "data/avatars/P000001.png"
patient_avatar_b64 = _read_avatar_b64(patient_avatar_rel)

def _doctor_avatar_b64(doctor_id: str | None) -> str | None:
    # Hook up your doctor avatars later if you like
    # For now, return None so we show initials
    return None

def _initials(text: str, fallback: str = "DR") -> str:
    s = (text or "").strip()
    if not s:
        return fallback
    parts = s.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return s[:2].upper()

# ---------------- Sidebar (threads) ----------------
with st.sidebar:
    st.subheader("Your threads")
    threads = svc.list_threads_by_patient(pid)
    labels = [f"#{t['id']} • {(t.get('doctor_id') or 'Doctor')} • {t.get('status','open')}" for t in threads]
    ix = 0 if labels else -1
    chosen = st.selectbox("Open thread", labels, index=ix) if labels else None
    chosen_id = int(chosen.split("•")[0].strip().lstrip("#")) if chosen else None

    st.divider()
    st.caption("Start a new conversation")
    c1, c2 = st.columns([3,1])
    with c1:
        new_doc = st.text_input("Doctor ID (optional)", placeholder="e.g., D000001")
    with c2:
        if st.button("New"):
            tid = svc.open_thread(pid, new_doc or None)
            st.session_state["active_thread"] = tid
            st.rerun()

active_thread_id = st.session_state.get("active_thread") or chosen_id
t = svc.get_thread(active_thread_id) if active_thread_id else (threads[0] if threads else None)
if t:
    active_thread_id = t["id"]

if not t:
    with card():
        st.info("No messages yet. Start a new thread from the sidebar.")
    st.stop()

# ---------------- Messenger-like CSS ----------------
st.markdown("""
<style>
/* Container */
.chat-wrap { max-width: 900px; margin: 0 auto; }

/* Day separator */
.day-sep { display:flex; align-items:center; gap:12px; margin: 16px 0; }
.day-sep .line { height:1px; background:rgba(255,255,255,.15); flex:1; }
.day-sep .label { font-size:12px; opacity:.75; }

/* Row + alignment */
.msg-row { display:flex; gap:10px; margin: 6px 0; align-items:flex-end; }
.msg-row.me   { flex-direction: row-reverse; }  /* right side (you) */
.msg-row.them { flex-direction: row; }          /* left side (doctor) */

/* Avatar */
.avatar { width:36px; height:36px; border-radius:999px; overflow:hidden;
          border:1px solid rgba(255,255,255,.12); background:#1E293B;
          display:flex; align-items:center; justify-content:center;
          font-weight:800; color:#C7D2FE; flex-shrink:0; }
.avatar img { width:100%; height:100%; object-fit:cover; }

/* Bubble */
.bubble { position:relative; max-width: 70%; padding:10px 14px; border-radius:18px;
          border:1px solid rgba(255,255,255,.12); word-wrap:break-word; }

/* Incoming (doctor) – Messenger gray */
.them .bubble {
  background:#e5e7eb; color:#111827; border-color:#e5e7eb;
}

/* Outgoing (you) – Messenger blue */
.me .bubble {
  background:#0084ff; color:#fff; border-color:#0084ff;
}

/* Tails */
.them .bubble::after,
.me .bubble::after {
  content:""; position:absolute; bottom:0; width:0; height:0; border:8px solid transparent;
}
.them .bubble::after {
  left:-4px; border-right-color:#e5e7eb; border-left:0; margin-bottom:-1px;
}
.me .bubble::after {
  right:-4px; border-left-color:#0084ff; border-right:0; margin-bottom:-1px;
}

/* Compressed stacks: hide avatar and tail on consecutive messages by same sender within 5 min */
.compact .avatar { visibility:hidden; }
.compact.them .bubble::after,
.compact.me .bubble::after { display:none; }

/* Meta */
.meta { font-size:11px; opacity:.65; margin-top:4px; text-align:right; }
.meta.left { text-align:left; }
</style>
""", unsafe_allow_html=True)

# ---------------- Helpers for grouping & formatting ----------------
def _is_same_sender(prev_role: str | None, cur_role: str | None) -> bool:
    return (prev_role or "") == (cur_role or "")

def _within(prev_ts: str | None, cur_ts: str | None, minutes: int = 5) -> bool:
    try:
        p = datetime.fromisoformat(prev_ts or "")
        c = datetime.fromisoformat(cur_ts or "")
        return abs((c - p).total_seconds()) <= minutes * 60
    except Exception:
        return False

def _date_label(ts: str | None) -> str:
    try:
        d = datetime.fromisoformat(ts or "").date()
    except Exception:
        return "Unknown date"
    today = datetime.now().date()
    if d == today:
        return "Today"
    if d == today - timedelta(days=1):
        return "Yesterday"
    return d.strftime("%A, %d %b %Y")

# ---------------- Header ----------------
with card(f"Thread #{t['id']} • {(t.get('doctor_id') or 'Doctor')} • {t.get('status','open').title()}"):
    st.write(f"Updated: {t.get('updated_at','—')}")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()
    with col2:
        if st.button("✅ Close", disabled=t.get("status") == "closed"):
            if svc.close_thread(t["id"]):
                st.success("Thread closed.")
                st.rerun()
    with col3:
        if st.button("📌 Set Active"):
            st.session_state["active_thread"] = t["id"]
            st.success("Active thread set.")

# ---------------- Conversation ----------------
msgs = list(t.get("messages", []))
# ensure chronological
msgs.sort(key=lambda m: m.get("timestamp",""))

with card():
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

    # Day separators + compact grouping
    prev_role, prev_ts, prev_date = None, None, None
    for i, m in enumerate(msgs):
        role = (m.get("sender_role") or "").lower()  # "patient" | "doctor"
        ts   = m.get("timestamp")
        text = m.get("text","")

        # Day separator
        cur_date = (ts or "")[:10]
        if cur_date != prev_date:
            label = _date_label(ts)
            st.markdown(f"""
                <div class="day-sep">
                    <div class="line"></div>
                    <div class="label">{label}</div>
                    <div class="line"></div>
                </div>
            """, unsafe_allow_html=True)
            prev_date = cur_date

        # Determine side and compactness
        is_me   = (role == "patient")  # patient messages on right
        side    = "me" if is_me else "them"
        compact = _is_same_sender(prev_role, role) and _within(prev_ts, ts, minutes=5)
        row_cls = f"msg-row {side}" + (" compact" if compact else "")

        # Choose avatar
        if is_me:
            if patient_avatar_b64 and not compact:
                avatar_html = f"<div class='avatar'><img src='data:image/png;base64,{patient_avatar_b64}'/></div>"
            elif compact:
                avatar_html = "<div class='avatar'></div>"
            else:
                avatar_html = f"<div class='avatar'>{_initials(profile.get('name','You'), 'YOU')}</div>"
        else:
            doc_id = t.get("doctor_id") or "Doctor"
            doc_b64 = _doctor_avatar_b64(doc_id)
            if doc_b64 and not compact:
                avatar_html = f"<div class='avatar'><img src='data:image/png;base64,{doc_b64}'/></div>"
            elif compact:
                avatar_html = "<div class='avatar'></div>"
            else:
                avatar_html = f"<div class='avatar'>{_initials(doc_id, 'DR')}</div>"

        # Bubble & meta
        # Escape minimal HTML (Streamlit won't auto-escape markdown inside our custom HTML)
        safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        meta_align = "" if is_me else "left"

        st.markdown(
            f"""
            <div class="{row_cls}">
                {avatar_html}
                <div class="bubble">
                    {safe_text}
                    <div class="meta {'left' if meta_align=='left' else ''}">{ts or ''}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        prev_role, prev_ts = role, ts

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Composer ----------------
with card("Send a message"):
    txt = st.text_area("Your message", height=90, placeholder="Write a message…")
    doc_id = st.text_input("Doctor ID (optional)", value=t.get("doctor_id",""))
    c_send, c_clear = st.columns([1,1])
    with c_send:
        if st.button("Send", type="primary"):
            ok, info = svc.send_patient_message(pid, txt, doctor_id=doc_id or None, thread_id=t["id"])
            if ok:
                st.success(f"Sent ✓ (thread #{info})")
                st.rerun()
            else:
                st.error(str(info))
    with c_clear:
        if st.button("Clear"):
            st.rerun()
