# counselor_name_pages/5_💬_Messages.py
import streamlit as st
from counselor_name_components.ui import apply_theme, top_nav, require_auth
from counselor_name_app.services.messaging import MessagingService
from counselor_name_app.services.patients import PatientService

st.set_page_config(page_title="Messages", page_icon="💬", layout="wide")
apply_theme(); require_auth(); top_nav("Messages")

svc = MessagingService()
me = st.session_state["auth_user"]

# -------------------- Tidy, aligned chat CSS --------------------
st.markdown("""
<style>
:root { --border:#1e2a3a; --card:#111b27; --muted:#9fb0c3; }
.chat-pane { background:var(--card); border:1px solid var(--border); border-radius:16px; padding:8px; }
.chat-scroll { max-height:540px; overflow-y:auto; padding:6px 8px 2px 8px; }
.row { display:flex; margin:8px 0; }
.row.me   { justify-content:flex-end; }
.row.them { justify-content:flex-start; }
.bubble { max-width:72%; padding:12px 14px; border-radius:16px; line-height:1.45; }
.bubble.me   { background:#17314d; border:1px solid #27425f; border-bottom-right-radius:6px; }
.bubble.them { background:#162332; border:1px solid #263244; border-bottom-left-radius:6px; }
.bubble.sys  { background:#221a1a; border:1px dashed #3b2a2a; color:#f6d7d7; max-width:60%;
               border-radius:10px; margin:0 auto; }
.meta { font-size:11px; opacity:.75; padding-top:4px; text-align:right; }
.thread { padding:12px; border:1px solid var(--border); border-radius:12px; background:var(--card); margin-bottom:10px; }
.thread.active { outline:1px solid #35507a; }
.thread .title { font-weight:700; }
.thread .preview { font-size:12px; color:var(--muted); margin-top:2px; }
.badge { display:inline-block; padding:1px 8px; border-radius:999px; font-size:11px; border:1px solid var(--border); background:#2a240f; }
.toolbar { display:flex; gap:10px; align-items:center; justify-content:flex-end; }
.divider { height:1px; background:var(--border); margin:12px 0; }
</style>
""", unsafe_allow_html=True)

# -------------------- State --------------------
if "active_thread" not in st.session_state:
    st.session_state["active_thread"] = None

# -------------------- Helpers --------------------
def recipient_picker():
    role = st.selectbox("Talk to", ["patient","admin","nurse","doctor","medstaff"])
    if role == "patient":
        plist = PatientService().list_assigned(me)
        if not plist:
            st.info("No assigned patients.")
            return None
        return st.selectbox("Recipient", options=[p["id"] for p in plist],
                            format_func=lambda x: next(p["name"] for p in plist if p["id"]==x))
    else:
        users = svc.users_by_role(role) if hasattr(svc, "users_by_role") else []
        if not users:
            st.info(f"No users found for role: {role}")
            return None
        return st.selectbox("Recipient", options=[u["id"] for u in users],
                            format_func=lambda x: next(u["name"] for u in users if u["id"]==x))

def display_thread_list():
    q = st.text_input("Search", placeholder="Name, title, or message text…")
    threads = []
    # Support both the advanced list_threads(user, query) and basic list_threads(user)
    try:
        threads = svc.list_threads(me, query=q.strip())  # advanced version
    except TypeError:
        # fallback to basic service
        raw = svc.list_threads(me)
        if q.strip():
            ql = q.lower()
            for t in raw:
                title = t.get("title","")
                text = " ".join(m.get("text","") for m in t.get("items",[]))
                names = " ".join(m for m in t.get("members",[]))
                if ql in (title + " " + text + " " + names).lower():
                    threads.append(t)
        else:
            threads = raw

    if not threads:
        st.info("No conversations yet.")
        return

    for t in threads:
        title = t.get("title") or "Conversation"
        last = (t.get("items", [])[-1]["text"] if t.get("items") else "")
        active = "active" if t.get("id")==st.session_state["active_thread"] else ""
        st.markdown(f"""
        <div class="thread {active}">
          <div class="title">{title}</div>
          <div class="preview">{last[:80]}{'…' if len(last)>80 else ''}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open", key=f"open_{t['id']}", use_container_width=True):
            st.session_state["active_thread"] = t["id"]
            # mark read if service supports it
            if hasattr(svc, "mark_read"):
                try: svc.mark_read(t["id"], me)
                except Exception: pass
            st.rerun()

# -------------------- Layout --------------------
left, right = st.columns([1.05, 2], gap="large")

with left:
    st.subheader("Threads")
    display_thread_list()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.subheader("New conversation")
    rec = recipient_picker()
    topic = st.text_input("Title (optional)", placeholder="e.g., Update on Nicole Tan")
    draft = st.text_area("Message…", key="new_msg", height=100)
    if st.button("Start chat", type="primary", use_container_width=True, disabled=not rec or not draft.strip()):
        members = [me, rec]
        # create or get thread if the service supports titles
        if hasattr(svc, "create_or_get_thread"):
            tid = svc.create_or_get_thread(topic.strip() or "Conversation", members)
            svc.post(tid, members, me, draft.strip(), title=topic.strip() or "Conversation")
        else:
            out = svc.post(None, members, me, draft.strip())
            tid = out.get("thread_id")
        st.session_state["active_thread"] = tid
        st.rerun()

with right:
    st.subheader("Conversation")

    # choose active (default to most recent)
    tid = st.session_state.get("active_thread")
    if not tid:
        ts = svc.list_threads(me)
        if ts:
            tid = ts[0]["id"]; st.session_state["active_thread"] = tid

    if not tid:
        st.info("Select a thread on the left or start a new conversation.")
        st.stop()

    # refresh live thread
    by_id = {t["id"]: t for t in svc.list_threads(me)}
    t = by_id.get(tid)
    if not t:
        st.info("Thread not found (might have been removed).")
        st.stop()

    # Header + rename
    title = t.get("title") or "Conversation"
    members_txt = ", ".join((getattr(svc, "name_of", lambda x: x)(m) for m in t.get("members", []) if m != me))
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown(f"**{title}**  \n<small class='muted'>with {members_txt}</small>", unsafe_allow_html=True)
    with c2:
        new_title = st.text_input("Rename", value=title, label_visibility="collapsed")
        if st.button("Save title", key=f"ttl_{tid}"):
            if hasattr(svc, "rename_thread"):
                svc.rename_thread(tid, new_title.strip() or "Conversation")
                st.rerun()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Chat viewport
    with st.container():
        st.markdown('<div class="chat-pane"><div class="chat-scroll">', unsafe_allow_html=True)
        for msg in t.get("items", []):
            who = "You" if msg["by"] == me else (getattr(svc, "name_of", lambda x: x)(msg["by"]))
            cls_row = "me" if msg["by"] == me else ("them" if msg["by"] != "system" else "")
            cls_bubble = "me" if msg["by"] == me else ("them" if msg["by"] != "system" else "sys")
            st.markdown(
                f"""
                <div class="row {cls_row}">
                  <div class="bubble {cls_bubble}">
                    <div>{msg['text']}</div>
                    <div class="meta">{who} · {msg['ts']}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown('</div></div>', unsafe_allow_html=True)

    # Composer
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.caption("Quick replies:")
    q1, q2, q3, q4 = st.columns(4)
    if q1.button("Acknowledged"):
        svc.post(tid, t["members"], me, "Acknowledged. Thanks for the update."); st.rerun()
    if q2.button("Following up"):
        svc.post(tid, t["members"], me, "Following up on this — any changes since our last message?"); st.rerun()
    if q3.button("Schedule call"):
        svc.post(tid, t["members"], me, "Can we schedule a quick call to discuss further?"); st.rerun()
    if q4.button("Share resources"):
        svc.post(tid, t["members"], me, "Sharing some resources that may help — let me know your thoughts."); st.rerun()

    msg = st.text_area("Type a message…", key=f"compose_{tid}", height=110, label_visibility="collapsed")
    s1, s2 = st.columns([1,1])
    if s1.button("Send", type="primary", key=f"send_{tid}"):
        if msg.strip():
            svc.post(tid, t["members"], me, msg.strip()); st.rerun()
    if s2.button("Simulate reply (other side)", key=f"sim_{tid}"):
        other = next((m for m in t["members"] if m != me), None)
        if other:
            svc.post(tid, t["members"], other, "Received. We will get back to you shortly."); st.rerun()
