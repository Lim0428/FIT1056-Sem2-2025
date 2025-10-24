# pages/1_👤_Profile_&_Preferences.py
import streamlit as st
from datetime import date, datetime
from components.ui import apply_theme, page_header, card, require_auth
from app.patient import PatientService
import os, io, base64
from pathlib import Path
try:
    from PIL import Image
except Exception:
    Image = None  # Pillow optional; we'll still save bytes if missing
from app.i18n import _


st.set_page_config(page_title="Profile", page_icon="👤", layout="centered")
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
    if not parts: return "👤"
    if len(parts) == 1: return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()

def _chip(label: str) -> str:
    return f"<span style='display:inline-block;padding:4px 10px;border-radius:999px;border:1px solid #D8E0F0;background:#F6F9FF;color:#1E2A44;font-size:12px;margin-right:6px;margin-bottom:6px;'>{label}</span>"
# Where to store avatars on disk
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
        # Resize to reasonable square (256px) to keep JSON lean when previewing as base64
        with Image.open(io.BytesIO(file_bytes)) as im:
            im = im.convert("RGB")
            im.thumbnail((256, 256))
            im.save(out_path, format="PNG", optimize=True)
    else:
        # If Pillow isn't available, just write the raw bytes (assuming it's already PNG)
        out_path.write_bytes(file_bytes)
    # Return a path relative to the project root of the patient app
    rel = f"data/avatars/{pid}.png"
    return rel

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

# ---------- VIEW MODE ----------
if not st.session_state.edit_profile:
    with card():
        # avatar + primary info
        cols = st.columns([1, 3])
        with card():
            # --- responsive row: photo | meta ---
            st.markdown("""
            <style>
            .prof-row{
                display:flex; align-items:center; gap:28px; 
                padding:4px 2px;
                flex-wrap:wrap;
            }
            .prof-photo{
                width: 240px;               /* bigger */
                height: 160px;              /* 3:2 rectangle */
                object-fit: cover;          /* crop-fill nicely */
                border-radius: 14px;        /* subtle rounded rectangle */
                border: 1px solid #D9E3F3;
                box-shadow: 0 6px 20px rgba(0,0,0,.08);
                background:#F2F6FF;
            }
            .prof-initials{
                width: 240px; height: 160px;
                border-radius: 14px;
                background: linear-gradient(135deg,#5EA1FF,#A8C5FF);
                color:#fff; font-weight:800; font-size:48px;
                display:flex; align-items:center; justify-content:center;
                border: 1px solid #D9E3F3;
                box-shadow: 0 6px 20px rgba(0,0,0,.08);
            }
            .prof-meta h2{
                margin:0 0 6px 0; font-size: 34px; font-weight: 800;
            }
            .prof-sub{ color:#56617A; margin-bottom:6px; font-weight:600; }
            .prof-note{ color:#7A8699; }
            @media (max-width: 820px){
                .prof-row{ align-items:flex-start; }
                .prof-photo,.prof-initials{ width: 100%; height: auto; max-width: 420px; }
            }
            </style>
            """, unsafe_allow_html=True)

            # Build the dynamic HTML
            avatar_rel = profile.get("avatar_path", "")
            b64 = read_avatar_b64(avatar_rel) if avatar_rel else None
            initials = _initials(profile.get("name", ""))

            dob_d = _parse_iso_date(profile.get("dob",""))
            sub = (
                f"<span><b>Patient ID:</b> {pid}</span>"
                f" &nbsp;&nbsp; | &nbsp;&nbsp; "
                f"<span><b>DOB:</b> {profile.get('dob','—')}</span>"
                f" &nbsp;&nbsp; | &nbsp;&nbsp; "
                f"<span><b>Age:</b> {_calc_age(dob_d)}</span>"
            )

            photo_html = (
                f"<img class='prof-photo' src='data:image/png;base64,{b64}' />"
                if b64 else
                f"<div class='prof-initials'>{initials}</div>"
            )

            st.markdown(
                f"""
                <div class="prof-row">
                {photo_html}
                <div class="prof-meta">
                    <h2>{profile.get('name','—')}</h2>
                    <div class="prof-sub">{sub}</div>
                    <div class="prof-note">Review your details or tap Edit to update.</div>
                </div>
                </div>
                """,
                unsafe_allow_html=True
            )


    with card("Details"):
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Gender:** {profile.get('gender','—')}")
            st.write(f"**Emergency contact:** {profile.get('emergency_contact','—')}")
            st.write(f"**Visibility:** {'Allowed to non-primary staff' if profile.get('visible_to_non_primary', False) else 'Restricted'}")
        with c2:
            st.write("**Medical details:**")
            st.caption(profile.get("medical_details","—") or "—")

    with card("Preferences"):
        chips = ""
        if profile.get("pref_language"):     chips += _chip(f"Language: {profile['pref_language']}")
        if profile.get("pref_food"):         chips += _chip(f"Food: {profile['pref_food']}")
        if profile.get("pref_nurse_gender"): chips += _chip(f"Nurse: {profile['pref_nurse_gender']}")
        if not chips:
            st.caption("No preferences saved yet.")
        else:
            st.markdown(chips, unsafe_allow_html=True)

    st.button("✏️ Edit profile", type="primary", on_click=lambda: st.session_state.update(edit_profile=True))
    st.stop()  # end view mode

# ---------- EDIT MODE ----------
with card("Edit profile"):
    name = st.text_input("Full name", value=profile.get("name",""))
    # calendar picker
    dob_default = _parse_iso_date(profile.get("dob",""))
    dob_calendar = st.date_input("Date of birth", value=dob_default if dob_default else None, max_value=date.today(), format="YYYY-MM-DD")
    gender = st.selectbox("Gender", ["", "Male", "Female", "Other"], index=["","Male","Female","Other"].index(profile.get("gender","")))
    med = st.text_area("Medical details (allergies, conditions)", value=profile.get("medical_details",""))
    emo = st.text_input("Emergency contact", value=profile.get("emergency_contact",""))
    st.markdown("**Profile photo**")
    up = st.file_uploader("Upload a JPG/PNG (optional)", type=["png","jpg","jpeg"], accept_multiple_files=False)
    col_prev, col_clear = st.columns([1,1])
    with col_prev:
        # live preview of uploaded image (not yet saved)
        if up is not None:
            st.image(up, caption="Preview", width=128)
        elif profile.get("avatar_path"):
            # show current saved avatar
            b64 = read_avatar_b64(profile["avatar_path"])
            if b64:
                st.image(io.BytesIO(base64.b64decode(b64)), caption="Current photo", width=128)
    with col_clear:
        clear_avatar = st.checkbox("Remove current photo")


with card("Preferences"):
    pref_food = st.text_input("Food preference", value=profile.get("pref_food",""))
    pref_lang = st.text_input("Preferred language", value=profile.get("pref_language",""))
    pref_nurse_gender = st.selectbox("Preferred nurse gender", ["", "Male", "Female"], index=["","Male","Female"].index(profile.get("pref_nurse_gender","")))
    vis = st.toggle("Allow non-primary staff to view my details", value=profile.get("visible_to_non_primary", False))

c_save, c_cancel = st.columns([1,1])
with c_save:
    if st.button("💾 Save changes", type="primary"):
            # Handle avatar persistence
        new_avatar_path = profile.get("avatar_path", "")
        if up is not None:
            bytes_data = up.getvalue()
            new_avatar_path = save_avatar_png(pid, bytes_data)
        if clear_avatar:
            # Remove file on disk if exists, and clear path
            try:
                if profile.get("avatar_path"):
                    (PAGES_DIR / ".." / profile["avatar_path"]).resolve().unlink(missing_ok=True)
            except Exception:
                pass
            new_avatar_path = ""

        ok = svc.update_profile(pid, {
            "name": name,
            "dob": dob_calendar.isoformat() if dob_calendar else "",
            "gender": gender,
            "medical_details": med,
            "emergency_contact": emo,
            "pref_food": pref_food,
            "pref_language": pref_lang,
            "pref_nurse_gender": pref_nurse_gender,
            "visible_to_non_primary": vis,
            "avatar_path": new_avatar_path,          # 👈 add this
        })
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
