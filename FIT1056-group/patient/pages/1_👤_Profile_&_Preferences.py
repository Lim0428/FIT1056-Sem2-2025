# pages/1_👤_Profile_&_Preferences.py
import streamlit as st
from datetime import date, datetime
# from components.ui import page_header   # (not used to avoid double header)
from components.ui import apply_theme, card, require_auth
from app.patient import PatientService
import io, base64
from pathlib import Path

try:
    from PIL import Image
except Exception:
    Image = None  # Pillow optional; we'll still save bytes if missing

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")
apply_theme()
require_auth()

# ---------- Colorful, dashboard-style UI ----------
st.markdown(
    """
    <style>
      :root{
        --bg:#0B1329; --bg2:#0A1124; --text:#F7FAFF; --muted:#E0EAFF;
        --c-blue:#7CB4FF; --c-teal:#2DD4BF; --c-green:#34D399; --c-pink:#EC4899;
        --c-orange:#FB923C; --c-purple:#A78BFA; --c-yellow:#FDE047;
        --field:#0F1A2E; --panel:#0D172B; --panel-border:rgba(255,255,255,.22);
        --hover:rgba(124,180,255,.18); --selected:rgba(124,180,255,.28);
      }
      [data-testid="stAppViewContainer"]{ background:var(--bg) !important; color:var(--text) !important; }
      section[data-testid="stSidebar"]{ background:var(--bg2) !important; color:var(--text) !important; }
      section[data-testid="stSidebar"] *{ color:var(--text) !important; }
      [data-testid="stAppViewContainer"] *{ color:var(--text) !important; }
      .stCaption, .muted { color: var(--muted) !important; opacity: .95 !important; }

      /* === HERO like Dashboard === */
      .pf-hero{
        margin-top:8px; margin-bottom:18px; padding:22px 26px;
        border-radius:20px;
        background:
          radial-gradient(100% 140% at 0% 0%, rgba(124,180,255,.35), transparent 60%),
          linear-gradient(135deg, #172947, #111B32 40%, #13203C);
        border:1px solid rgba(255,255,255,.14);
        box-shadow: 0 26px 60px rgba(0,0,0,.55);
      }
      .pf-hero h1{ margin:0; font-size:42px; font-weight:900; letter-spacing:.3px; color:#F8FBFF; }
      .pf-hero .sub{ color:#D7E4FF; opacity:.98; margin-top:6px; font-weight:600; }
      .pf-hero .bar{
        height:6px; width:100%; border-radius:999px; margin-top:14px;
        background: linear-gradient(90deg, var(--c-blue), var(--c-teal), var(--c-green),
                                    var(--c-yellow), var(--c-orange), var(--c-pink), var(--c-purple));
        box-shadow: 0 8px 24px rgba(124,180,255,.25);
      }

      /* Inputs / textareas */
      .stTextInput > div > div > input,
      .stTextArea textarea,
      .stDateInput > div > input{
        background: var(--field) !important;
        color:#EAF2FF !important;
        border:1px solid rgba(255,255,255,.20) !important;
      }

      /* Selectbox control (main pill) */
      [data-testid="stSelectbox"] div[data-baseweb="select"] > div{
        background: var(--field) !important;
        border: 1px solid rgba(255,255,255,.20) !important;
      }
      [data-testid="stSelectbox"] div[data-baseweb="select"] *{ color:#EAF2FF !important; }
      [data-testid="stSelectbox"] div[data-baseweb="select"] div[class*="placeholder"]{
        color:#9FB0C3 !important; opacity:1 !important;
      }
      [data-testid="stSelectbox"] svg{ color:#EAF2FF !important; fill:#EAF2FF !important; }

      /* Dropdown panels (options) — force dark + vivid hover/selected */
      div[data-baseweb="popover"] *{ color:#EAF2FF !important; }
      div[data-baseweb="popover"] div, div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li{
        background: var(--panel) !important;
      }
      [role="listbox"]{ background:var(--panel) !important; border:1px solid var(--panel-border) !important; }
      [role="option"]{ color:#EAF2FF !important; }
      [role="option"]:hover{ background: var(--hover) !important; }
      [role="option"][aria-selected="true"]{ background: var(--selected) !important; }

      /* react-select fallbacks (older Streamlit builds) */
      .css-26l3qy-menu, .css-1n7v3ny-menu, .css-1okebmr-menu{
        background: var(--panel) !important; border:1px solid var(--panel-border) !important;
      }
      .css-1n7v3ny-option, .css-10wo9uf-option, .css-yt9ioa-option, .css-1ezz8as-option{
        background: var(--panel) !important; color:#EAF2FF !important;
      }
      .css-1n7v3ny-option:hover, .css-10wo9uf-option:hover, .css-yt9ioa-option:hover, .css-1ezz8as-option:hover{
        background: var(--hover) !important;
      }
      .css-1n7v3ny-option[aria-selected="true"], .css-10wo9uf-option[aria-selected="true"]{
        background: var(--selected) !important;
      }

      /* Profile header card */
      .pf-card{ display:flex; gap:22px; align-items:center; width:100%; }
      .pf-photo{
        width:280px; height:180px; object-fit:cover;
        border-radius:14px; border:1px solid rgba(255,255,255,.12);
        box-shadow: 0 12px 30px rgba(0,0,0,.45);
        background:#111B32; overflow:hidden;
      }
      .pf-initials{
        width:280px; height:180px; display:flex; align-items:center; justify-content:center;
        border-radius:14px; color:#fff; font-weight:900; font-size:46px;
        border:1px solid rgba(255,255,255,.12);
        box-shadow:0 12px 30px rgba(0,0,0,.45);
        background: radial-gradient(120% 120% at 0% 0%, rgba(124,180,255,.55), transparent 60%), rgba(124,180,255,.12);
      }
      .pf-main h2{ margin:0 0 6px 0; font-size:36px; font-weight:900; letter-spacing:.2px; }
      .pf-sub{ color:#D8E6FF; opacity:.9; margin-bottom:10px; font-weight:700; }
      .pf-desc{ color:#CFE0FF; opacity:.9; }

      /* Fancy chips */
      .chip{
        display:inline-block; padding:6px 12px; border-radius:999px; margin:0 8px 8px 0;
        font-size:12px; font-weight:800; letter-spacing:.2px;
        background: linear-gradient(90deg, rgba(45,212,191,.18), rgba(124,180,255,.18));
        border:1px solid rgba(124,180,255,.35);
        box-shadow:0 0 10px rgba(124,180,255,.18);
      }
      .chip.green { background:linear-gradient(90deg, rgba(52,211,153,.20), rgba(45,212,191,.15)); border-color:rgba(52,211,153,.40); }
      .chip.orange{ background:linear-gradient(90deg, rgba(251,146,60,.18), rgba(253,224,71,.18));  border-color:rgba(251,146,60,.38); }

      @media (max-width: 900px){
        .pf-card{ flex-direction:column; align-items:flex-start; }
        .pf-photo, .pf-initials{ width:100%; height:auto; max-height:220px; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- HERO banner (to match Daily Survey/Dashboard) ---
st.markdown(
    """
    <div class="pf-hero">
      <h1>Profile & Preferences</h1>
      <div class="sub">Update your information</div>
      <div class="bar"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

svc = PatientService()
pid = st.session_state["auth_user"]
profile = svc.get(pid) or {}

# ---------- helpers ----------
def _parse_iso_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def _calc_age(d: date | None) -> str:
    if not d:
        return "—"
    today = date.today()
    years = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    return f"{years}"

def _initials(name: str) -> str:
    parts = [p for p in (name or "").strip().split() if p]
    if not parts:
        return "👤"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()

def _chip(label: str, cls: str = "") -> str:
    cls = f" {cls}" if cls else ""
    return f"<span class='chip{cls}'>{label}</span>"

# Where to store avatars on disk (repo-level data/avatars)
PAGES_DIR = Path(__file__).resolve().parent
DATA_DIR = (PAGES_DIR / ".." / "data").resolve()
AVATAR_DIR = DATA_DIR / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

def save_avatar_png(pid: str, file_bytes: bytes) -> str:
    out_path = AVATAR_DIR / f"{pid}.png"
    if Image:
        with Image.open(io.BytesIO(file_bytes)) as im:
            im = im.convert("RGB")
            im.thumbnail((512, 512))
            im.save(out_path, format="PNG", optimize=True)
    else:
        out_path.write_bytes(file_bytes)
    return f"data/avatars/{pid}.png"

def read_avatar_b64(rel_path: str) -> str | None:
    try:
        full = (PAGES_DIR / ".." / rel_path).resolve()
        data = full.read_bytes()
        return base64.b64encode(data).decode("utf-8")
    except Exception:
        return None

def read_avatar_bytes(rel_path: str) -> bytes | None:
    try:
        full = (PAGES_DIR / ".." / rel_path).resolve()
        return full.read_bytes()
    except Exception:
        return None

# UI state
if "edit_profile" not in st.session_state:
    st.session_state.edit_profile = False

# =============== VIEW MODE (Compact Card) ===============
if not st.session_state.edit_profile:
    with card():
        avatar_rel = profile.get("avatar_path", "")
        b64 = read_avatar_b64(avatar_rel) if avatar_rel else None
        initials = _initials(profile.get("name", ""))

        dob_d = _parse_iso_date(profile.get("dob", ""))
        meta_line = (
            f"<b>Patient ID:</b> {pid} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>DOB:</b> {profile.get('dob','—')} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Age:</b> {_calc_age(dob_d)}"
        )

        photo_html = (
            f"<img class='pf-photo' src='data:image/png;base64,{b64}'/>"
            if b64 else f"<div class='pf-initials'>{initials}</div>"
        )

        st.markdown(
            f"""
            <div class="pf-card">
              {photo_html}
              <div class="pf-main">
                <h2>{profile.get('name','—')}</h2>
                <div class="pf-sub">{meta_line}</div>
                <div class="pf-desc">Review your details or tap Edit to update.</div>
                <div style="margin-top:12px;">
                  {_chip('Language: ' + (profile.get('pref_language') or '—'))}
                  {_chip('Food: ' + (profile.get('pref_food') or '—'), 'green')}
                  {_chip('Preferred nurse: ' + (profile.get('pref_nurse_gender') or '—'), 'orange')}
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with card("Details"):
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Gender:** {profile.get('gender','—')}")
            st.write(f"**Emergency contact:** {profile.get('emergency_contact','—')}")
            st.write(
                f"**Visibility:** {'Allowed to non-primary staff' if profile.get('visible_to_non_primary', False) else 'Restricted'}"
            )
        with c2:
            st.write("**Medical details:**")
            st.caption(profile.get("medical_details", "—") or "—")

    with card("Preferences"):
        chips = ""
        if profile.get("pref_language"):
            chips += _chip(f"Language: {profile['pref_language']}")
        if profile.get("pref_food"):
            chips += _chip(f"Food: {profile['pref_food']}", "green")
        if profile.get("pref_nurse_gender"):
            chips += _chip(f"Nurse: {profile['pref_nurse_gender']}", "orange")
        if not chips:
            st.caption("No preferences saved yet.")
        else:
            st.markdown(chips, unsafe_allow_html=True)

    st.button("✏️ Edit profile", type="primary", on_click=lambda: st.session_state.update(edit_profile=True))
    st.stop()  # end view mode

# =============== EDIT MODE ===============
with card("Edit profile"):
    name = st.text_input("Full name", value=profile.get("name", ""))

    dob_default = _parse_iso_date(profile.get("dob", ""))
    dob_calendar = st.date_input(
        "Date of birth",
        value=dob_default if dob_default else None,
        min_value=date(1900, 1, 1),
        max_value=date.today(),
        format="YYYY-MM-DD",
    )

    gender = st.selectbox(
        "Gender",
        ["", "Male", "Female", "Other"],
        index=["", "Male", "Female", "Other"].index(profile.get("gender", "")),
    )
    med = st.text_area("Medical details (allergies, conditions)", value=profile.get("medical_details", ""))
    emo = st.text_input("Emergency contact", value=profile.get("emergency_contact", ""))

    st.markdown("**Profile photo**")
    up = st.file_uploader("Upload a JPG/PNG (optional)", type=["png","jpg","jpeg"], accept_multiple_files=False)

    col_prev, col_clear = st.columns([1, 1])
    with col_prev:
        if profile.get("avatar_path"):
            _bytes = read_avatar_bytes(profile["avatar_path"])
            if _bytes:
                st.image(_bytes, caption="Current photo", width=160)
            else:
                st.caption("Current photo not found.")
    with col_clear:
        clear_avatar = st.checkbox("Remove current photo")

    new_avatar_path = profile.get("avatar_path", "")
    if up is not None:
        ok_avatar = PatientService().set_avatar(pid, up.read(), up.name)
        if ok_avatar:
            profile = PatientService().get(pid) or {}
            new_avatar_path = profile.get("avatar_path","")
        else:
            st.error("Failed to save avatar")
    if clear_avatar:
        new_avatar_path = ""

with card("Preferences"):
    pref_food = st.text_input("Food preference", value=profile.get("pref_food", ""))
    pref_lang = st.text_input("Preferred language", value=profile.get("pref_language", ""))
    pref_nurse_gender = st.selectbox(
        "Preferred nurse gender",
        ["", "Male", "Female"],
        index=["", "Male", "Female"].index(profile.get("pref_nurse_gender", "")),
    )
    vis = st.toggle("Allow non-primary staff to view my details", value=profile.get("visible_to_non_primary", False))

c_save, c_cancel = st.columns([1, 1])
with c_save:
    if st.button("💾 Save changes", type="primary"):
        new_avatar_path = profile.get("avatar_path", "")
        if up is not None:
            bytes_data = up.getvalue()
            new_avatar_path = save_avatar_png(pid, bytes_data)
        if clear_avatar:
            try:
                if profile.get("avatar_path"):
                    (PAGES_DIR / ".." / profile["avatar_path"]).resolve().unlink(missing_ok=True)
            except Exception:
                pass
            new_avatar_path = ""

        ok = PatientService().update_profile(
            pid,
            {
                "name": name,
                "dob": dob_calendar.isoformat() if dob_calendar else "",
                "gender": gender,
                "medical_details": med,
                "emergency_contact": emo,
                "pref_food": pref_food,
                "pref_language": pref_lang,
                "pref_nurse_gender": pref_nurse_gender,
                "visible_to_non_primary": vis,
                "avatar_path": new_avatar_path,
            },
        )
        if ok:
            st.success("Profile updated.")
            st.session_state.edit_profile = False
            st.rerun()
        else:
            st.error("Save failed.")
with c_cancel:
    if st.button("✖️ Cancel"):
        st.session_state.edit_profile = False
        st.rerun()
