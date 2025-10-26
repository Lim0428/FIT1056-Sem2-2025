# carelog_nurse/pages/6_👩‍⚕️_Profile.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd

from components.ui import apply_theme, page_header
from app.nurse_service import NurseService

# -------------------- Config / Paths --------------------
st.set_page_config(page_title="Nurse Profile", page_icon="👩‍⚕️", layout="wide")
apply_theme()

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
NURSES_PATH = DATA_DIR / "nurses.json"
PATIENTS_PATH = DATA_DIR / "patients.json"
FEEDBACK_PATH = DATA_DIR / "nurse_feedback.json"  # patient -> nurse feedback

DEFAULT_NURSE_ID = "nurse_001"  # until login is wired

# -------------------- IO helpers --------------------
def _load_json(path: Path, default):
    try:
        if not path.exists() or path.stat().st_size == 0: return default
        txt = path.read_text(encoding="utf-8").strip()
        if txt in {"", "[]", "{}", "null"}: return default
        return json.loads(txt)
    except Exception:
        return default

def _save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def _get_nurse(nid: str):
    nurses = _load_json(NURSES_PATH, [])
    for n in nurses:
        if n.get("id") == nid:
            return n
    return {"id": nid, "name": "Nurse", "email": "", "phone": "", "avatar": ""}

def _upsert_nurse(record: dict):
    nurses = _load_json(NURSES_PATH, [])
    for i, n in enumerate(nurses):
        if n.get("id") == record["id"]:
            nurses[i] = record
            _save_json(NURSES_PATH, nurses)
            return
    nurses.append(record)
    _save_json(NURSES_PATH, nurses)

def _patients_for_nurse(nid: str):
    rows = _load_json(PATIENTS_PATH, [])
    return [p for p in rows if p.get("assigned_to") == nid or p.get("assigned_nurse_id") == nid]

def _feedback_for_nurse(nid: str):
    rows = _load_json(FEEDBACK_PATH, [])
    return [r for r in rows if r.get("nurse_id") == nid]

def _avg_rating(rows):
    if not rows: return 0.0
    vals = [r.get("rating") or 0 for r in rows]
    return round(sum(vals) / len(vals), 2)

def _rerun():
    try: st.rerun()
    except AttributeError:
        try: st.experimental_rerun()
        except Exception: pass

# -------------------- Card-style CSS --------------------
st.markdown("""
<style>
  :root { --bg:#0a1524; --ink:#ffffff; --muted:#cfe0ff; --edge:#2f4f7f; --card:#0d1a2d; --input:#0c1b30; --inputEdge:#3a5e96; }
  body, div, p, span, small, strong, label { color:var(--ink)!important; }
  ::placeholder { color:var(--muted)!important; opacity:1; }

  .card { background:var(--card); border:1px solid var(--edge); border-radius:18px;
          padding:16px; box-shadow:0 10px 30px rgba(0,0,0,.35); }
  .soft { background:var(--bg); }  /* subtle container */
  .title { font-weight:900; font-size:16px; margin-bottom:10px; color:#fff; }

  input, textarea, select {
    background:var(--input)!important; color:#fff!important;
    border:1px solid var(--inputEdge)!important; border-radius:10px!important;
  }
  [data-baseweb="select"]>div, [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input {
    background:var(--input)!important; color:#fff!important; border:1px solid var(--inputEdge)!important;
  }
  .stButton>button {
    border:1px solid #5b8bda; background:#2a4f8a; color:#fff; padding:8px 14px; border-radius:10px; font-weight:800;
    box-shadow:0 6px 16px rgba(0,0,0,.35);
  }
  .stButton>button:hover { background:#3564b3; border-color:#7fb0ff; }

  /* Hero profile card */
  .hero { display:flex; gap:18px; align-items:center; }
  .avatar { width:96px; height:96px; border-radius:999px; border:2px solid #4b78bf;
            object-fit:cover; background:#0d1a2d; display:block; }
  .name { font-size:22px; font-weight:900; line-height:1.1; }
  .id { color:#cfe0ff; font-size:12px; }
  .chips { display:flex; gap:8px; flex-wrap:wrap; margin-top:6px; }
  .chip { display:inline-block; padding:4px 10px; border-radius:999px; background:#1a2f4d; color:#fff; font-size:11px; border:1px solid #4b78bf; }

  .kpi { text-align:center; }
  .kpi .num { font-size:26px; font-weight:900; }
  .kpi .lbl { color:#cfe0ff; font-size:12px; letter-spacing:.05em; text-transform:uppercase; }

  .rating { color:#ffd166; font-size:18px; letter-spacing:2px; }

  /* Feedback cards */
  .fb { background:#0b1a2f; border:1px solid #2f4f7f; border-radius:14px; padding:12px; margin-bottom:10px; }
  .meta { color:#cfe0ff; font-size:12px; margin-bottom:4px; }
</style>
""", unsafe_allow_html=True)

page_header("Nurse Profile", "Compact card style • personal info • patient feedback", "👩‍⚕️")

# -------------------- Data --------------------
svc = NurseService()
nurse_id = st.session_state.get("nurse_id", DEFAULT_NURSE_ID)

nurse = _get_nurse(nurse_id)
assigned = _patients_for_nurse(nurse_id)
feedback = sorted(_feedback_for_nurse(nurse_id), key=lambda r: r.get("created_at",""), reverse=True)
avg_rating = _avg_rating(feedback)

# -------------------- HERO PROFILE CARD --------------------
st.markdown('<div class="card hero">', unsafe_allow_html=True)

avatar_rel = nurse.get("avatar") or ""
avatar_abs = (DATA_DIR / avatar_rel) if avatar_rel else None
left, mid, right = st.columns([0.25, 1.2, 1])

with left:
    if avatar_abs and avatar_abs.exists():
        st.image(str(avatar_abs), width=96)
    else:
        initials = "".join([x[:1] for x in (nurse.get("name") or "Nurse").split()][:2]).upper()
        st.markdown(f"<div class='avatar' style='display:flex;align-items:center;justify-content:center;font-weight:900;font-size:34px;'>{initials}</div>", unsafe_allow_html=True)

with mid:
    st.markdown(f"<div class='name'>{nurse.get('name','Nurse')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='id'>ID: {nurse_id}</div>", unsafe_allow_html=True)
    stars = "★"*int(round(avg_rating)) + "☆"*(5-int(round(avg_rating)))
    st.markdown(f"<div class='rating' style='margin-top:4px'>{stars}</div>", unsafe_allow_html=True)
    # KPI chips
    try:
        open_tasks = len([t for t in svc.list_tasks() if t.get("status","").lower() not in {"done","completed"}])
    except Exception:
        open_tasks = 0
    st.markdown("<div class='chips'>"
                f"<span class='chip'>Patients: {len(assigned)}</span>"
                f"<span class='chip'>Open tasks: {open_tasks}</span>"
                f"<span class='chip'>Avg rating: {avg_rating:.2f}</span>"
                "</div>", unsafe_allow_html=True)

with right:
    k1, k2, k3 = st.columns(3)
    k1.markdown("<div class='kpi'><div class='num'>"+str(len(assigned))+"</div><div class='lbl'>Assigned</div></div>", unsafe_allow_html=True)
    k2.markdown("<div class='kpi'><div class='num'>"+str(open_tasks)+"</div><div class='lbl'>Open Tasks</div></div>", unsafe_allow_html=True)
    k3.markdown("<div class='kpi'><div class='num'>"+f"{avg_rating:.2f}"+"</div><div class='lbl'>Avg Rating</div></div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
st.write("")  # spacing

# -------------------- CARDS ROW --------------------
col1, col2 = st.columns([1, 1.2])

# ---- Contact / Personal Info Card (read-only → edit) ----
with col1:
    st.markdown('<div class="card soft">', unsafe_allow_html=True)
    st.markdown("<div class='title'>Contact & Personal Info</div>", unsafe_allow_html=True)

    if "profile_edit" not in st.session_state:
        st.session_state["profile_edit"] = False

    if not st.session_state["profile_edit"]:
        st.markdown(f"**Full name:** {nurse.get('name','Nurse')}")
        st.markdown(f"**Email:** {nurse.get('email','—')}")
        st.markdown(f"**Phone:** {nurse.get('phone','—')}")
        st.markdown("")
        if st.button("Edit"):
            st.session_state["profile_edit"] = True
            _rerun()
    else:
        c1, c2 = st.columns([1, 1])
        with c1:
            name = st.text_input("Full name", value=nurse.get("name","Nurse"), key="pf_name")
            phone = st.text_input("Phone", value=nurse.get("phone",""), key="pf_phone")
        with c2:
            email = st.text_input("Email", value=nurse.get("email",""), key="pf_email")
            up = st.file_uploader("Avatar (png/jpg)", type=["png","jpg","jpeg"], key="pf_avatar")

        s1, s2 = st.columns([1,1])
        if s1.button("Save"):
            nurse["name"] = (name or "Nurse").strip()
            nurse["email"] = email.strip()
            nurse["phone"] = phone.strip()
            if up is not None:
                UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
                new_name = f"avatar_{nurse_id}.png"
                (UPLOAD_DIR / new_name).write_bytes(up.read())
                nurse["avatar"] = f"uploads/{new_name}"
            _upsert_nurse(nurse)
            st.session_state["profile_edit"] = False
            st.success("Profile updated.")
            _rerun()
        if s2.button("Cancel"):
            st.session_state["profile_edit"] = False
            _rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ---- Feedback Card (patient → nurse) ----
with col2:
    st.markdown('<div class="card soft">', unsafe_allow_html=True)
    st.markdown("<div class='title'>Patient Feedback</div>", unsafe_allow_html=True)

    if not feedback:
        st.info("No feedback from patients yet.")
    else:
        for r in feedback[:25]:
            ts = r.get("created_at","")
            pid = r.get("patient_id","")
            rt = int(r.get("rating", 0) or 0)
            stars = "★"*rt + "☆"*(5-rt)
            st.markdown(
                f"<div class='fb'>"
                f"<div class='meta'>{ts} · Patient: <b>{pid}</b></div>"
                f"<div class='rating' style='margin:2px 0 6px 0'>{stars}</div>"
                f"<div>{(r.get('text') or '').replace(chr(10), '<br>')}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        # Export
        df = pd.DataFrame([{
            "Date": r.get("created_at",""),
            "Patient": r.get("patient_id",""),
            "Rating": r.get("rating",""),
            "Comment": r.get("text",""),
        } for r in feedback])
        st.download_button(
            "⬇️ Download feedback (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"nurse_{nurse_id}_feedback.csv",
            mime="text/csv"
        )

    st.markdown('</div>', unsafe_allow_html=True)

# Footer hint
st.caption("ℹ️ Profile reads/writes `nurses.json`. Feedback is patient-submitted in `nurse_feedback.json`.")
