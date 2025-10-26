# pages/1_👤_Profile_&_Preferences.py
import streamlit as st
from datetime import date, datetime
from components.ui import apply_theme, page_header, card, require_auth
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
page_header("Profile & Preferences", "Update your information", "👤")

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

def _chip(label: str) -> str:
    return (
        "<span style='display:inline-block;padding:6px 12px;border-radius:999px;"
        "border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.06);"
        "color:#EAF2FF;font-size:12px;margin-right:8px;margin-bottom:6px;'>"
        f"{label}</span>"
    )

# Where to store avatars on disk (repo-level data/avatars)
PAGES_DIR = Path(__file__).resolve().parent
DATA_DIR = (PAGES_DIR / ".." / "data").resolve()
AVATAR_DIR = DATA_DIR / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

def save_avatar_png(pid: str, file_bytes: bytes) -> str:
    """
    Save uploaded bytes as a small PNG avatar under data/avatars/{pid}.png
    Returns a relative path string like 'data/avatars/P000001.png'
    """
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

# UI state
if "edit_profile" not in st.session_state:
    st.session_state.edit_profile = False

# =============== VIEW MODE (Compact Card) ===============
if not st.session_state.edit_profile:
    with card():
        st.markdown(
            """
            <style>
              .pf-card{
                display:flex; gap:22px; align-items:center;
                width:100%;
              }
              .pf-photo{
                width: 280px;
                height: 180px;
                object-fit: cover;
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,.10);
                box-shadow: 0 10px 30px rgba(0,0,0,.35);
                background:#1A2234;
                overflow: hidden;
              }
              .pf-initials{
                width:280px; height:180px;
                display:flex; align-items:center; justify-content:center;
                border-radius: 14px;
                background: linear-gradient(135deg,#6CA8FF,#9EAFFF);
                color:#fff; font-weight:900; font-size:46px;
                border: 1px solid rgba(255,255,255,.12);
                box-shadow: 0 10px 30px rgba(0,0,0,.35);
              }
              .pf-main h2{
                margin:0 0 6px 0; font-size: 36px; font-weight: 900; color:#FFFFFF;
                letter-spacing:.2px;
              }
              .pf-sub{
                color:#D8E6FF; opacity:.85; margin-bottom:10px; font-weight:600;
              }
              .pf-desc{
                color:#CFE0FF; opacity:.85;
              }
              @media (max-width: 900px){
                .pf-card{ flex-direction:column; align-items:flex-start; }
                .pf-photo, .pf-initials{ width:100%; height:auto; max-height:220px; }
              }
            </style>
            """,
            unsafe_allow_html=True,
        )

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
            if b64
            else f"<div class='pf-initials'>{initials}</div>"
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
                    {_chip('Food: ' + (profile.get('pref_food') or '—'))}
                    {_chip('Preferred nurse: ' + (profile.get('pref_nurse_gender') or '—'))}
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
            chips += _chip(f"Food: {profile['pref_food']}")
        if profile.get("pref_nurse_gender"):
            chips += _chip(f"Nurse: {profile['pref_nurse_gender']}")
        if not chips:
            st.caption("No preferences saved yet.")
        else:
            st.markdown(chips, unsafe_allow_html=True)

    st.button("✏️ Edit profile", type="primary", on_click=lambda: st.session_state.update(edit_profile=True))
    st.stop()  # end view mode

# =============== EDIT MODE ===============
with card("Edit profile"):
    name = st.text_input("Full name", value=profile.get("name", ""))

    # Allow much earlier years:
    dob_default = _parse_iso_date(profile.get("dob", ""))
    dob_calendar = st.date_input(
        "Date of birth",
        value=dob_default if dob_default else None,
        min_value=date(1900, 1, 1),   # <-- allow earlier selection
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

    # --- Avatar uploader block (correct, repo-root) ---
    st.markdown("**Profile photo**")
    up = st.file_uploader("Upload a JPG/PNG (optional)", type=["png","jpg","jpeg"], accept_multiple_files=False)

    col_prev, col_clear = st.columns([1, 1])
    with col_prev:
        # Just show the file referenced in JSON (Streamlit will resolve relative path from repo root)
        if profile.get("avatar_path"):
            st.image(profile["avatar_path"], caption="Current photo", width=160)
    with col_clear:
        clear_avatar = st.checkbox("Remove current photo")

    # inside your Save button handler:
    new_avatar_path = profile.get("avatar_path", "")
    if up is not None:
        # This writes the image into FIT1056-GROUP/data/avatars/<PID>.<ext>
        # and updates patients[PID]["avatar_path"] in data/patient.json
        ok_avatar = svc.set_avatar(pid, up.read(), up.name)
        if ok_avatar:
            # refresh the profile data and use the new value from JSON
            profile = svc.get(pid) or {}
            new_avatar_path = profile.get("avatar_path","")
        else:
            st.error("Failed to save avatar")
    if clear_avatar:
        # clear the JSON field (optional: also remove the file if you want)
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
        # Handle avatar persistence
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

        ok = svc.update_profile(
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
