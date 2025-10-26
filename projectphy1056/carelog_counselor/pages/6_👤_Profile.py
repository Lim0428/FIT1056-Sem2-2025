# counselor_name_pages/6_👤_Profile.py
import io
from pathlib import Path
from datetime import time
import streamlit as st

from counselor_name_components.ui import apply_theme, top_nav, require_auth
from counselor_name_app.repository import Repo
from counselor_name_app.services.identity import IdentityService

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")
apply_theme(); require_auth(); top_nav("Profile")

repo = Repo()
db = repo.read()
me = st.session_state["auth_user"]
user = db.get("users", {}).get(me, {})

# ---------- helpers ----------
SPECIALTY_OPTIONS = [
    "Anxiety", "Depression", "Trauma/PTSD", "Grief", "Stress",
    "Relationship", "Addiction", "Child/Adolescent", "LGBTQIA+",
    "OCD", "Bipolar", "Sleep", "Eating Disorders"
]

DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def as_timespan(t: time | None) -> str:
    return t.strftime("%H:%M") if t else ""

def save_user(updated: dict):
    db.setdefault("users", {})[me] = updated
    repo.write(db)

def avatar_dir() -> Path:
    # store avatars under project data/
    p = repo.data_dir / "avatars"
    p.mkdir(parents=True, exist_ok=True)
    return p

def save_avatar(upload) -> str:
    if not upload:
        return user.get("avatar_path","")
    ext = Path(upload.name).suffix.lower() or ".png"
    fname = f"{me}{ext}"
    path = avatar_dir() / fname
    path.write_bytes(upload.read())
    return str(path)

# ---------- header ----------
colA, colB = st.columns([1, 3], gap="large")
with colA:
    st.markdown("#### Profile")
    st.caption(f"Counselor ID: **{me}**")
    # Avatar
    st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)
    st.caption("Avatar")
    avatar_file = st.file_uploader("Upload image", type=["png","jpg","jpeg"], label_visibility="collapsed")
    if avatar_file:
        st.image(avatar_file, caption="Preview", use_column_width=True)
        if st.button("Save avatar", use_container_width=True):
            path = save_avatar(avatar_file)
            user["avatar_path"] = path
            save_user(user)
            st.success("Avatar saved."); st.rerun()
    else:
        if user.get("avatar_path") and Path(user["avatar_path"]).exists():
            st.image(user["avatar_path"], caption="Current avatar", use_column_width=True)
        else:
            st.info("No avatar yet. Upload a PNG/JPG.")

with colB:
    st.markdown("#### Professional Details")
    c1, c2 = st.columns(2)
    name = c1.text_input("Full name", value=user.get("name",""))
    email = c2.text_input("Email", value=user.get("email",""))
    license_no = c1.text_input("License No.", value=user.get("license",""))
    contact = c2.text_input("Contact number", value=user.get("contact",""))

    st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

    # Specialties & bio
    specialties = st.multiselect(
        "Specialties",
        options=SPECIALTY_OPTIONS,
        default=[s for s in user.get("specialties", []) if s in SPECIALTY_OPTIONS],
        help="Pick your common areas. You can also add custom tags below."
    )
    extra = st.text_input("Add custom specialties (comma separated)", placeholder="e.g., Perinatal Mental Health, Burnout")
    if extra.strip():
        specialties += [t.strip() for t in extra.split(",") if t.strip()]

    bio = st.text_area(
        "Short bio",
        placeholder="1–3 sentences about your approach, training, and what clients can expect.",
        value=user.get("bio",""),
        height=100
    )

    st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

    # Availability (simple weekly schedule)
    st.markdown("##### Availability")
    av_cols = st.columns(3)
    hours = user.get("hours_detail", {d: {"start":"09:00","end":"17:00","on": d in ["Mon","Tue","Wed","Thu","Fri"]} for d in DAYS})
    new_hours = {}
    for i, d in enumerate(DAYS):
        with av_cols[i % 3]:
            on = st.toggle(f"{d}", value=bool(hours.get(d,{}).get("on", False)))
            s = st.time_input(f"{d} start", value=time.fromisoformat(hours.get(d,{}).get("start","09:00")), label_visibility="collapsed", key=f"s_{d}")
            e = st.time_input(f"{d} end", value=time.fromisoformat(hours.get(d,{}).get("end","17:00")), label_visibility="collapsed", key=f"e_{d}")
            new_hours[d] = {"on": on, "start": as_timespan(s), "end": as_timespan(e)}

    pretty_hours = ", ".join([f"{d} {h['start']}-{h['end']}" for d,h in new_hours.items() if h["on"]]) or "—"
    st.caption(f"Working hours summary: {pretty_hours}")

    st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

    # Preferences
    st.markdown("##### Notifications & Preferences")
    prefs = user.get("preferences", {"email_notifications": True, "desktop_notifications": False, "show_patient_ids": True})
    p1, p2, p3 = st.columns(3)
    email_notif = p1.toggle("Email notifications", value=bool(prefs.get("email_notifications", True)))
    desk_notif = p2.toggle("Desktop notifications", value=bool(prefs.get("desktop_notifications", False)))
    show_ids   = p3.toggle("Show patient IDs", value=bool(prefs.get("show_patient_ids", True)))

    # Save main profile
    if st.button("Save Profile", type="primary"):
        # minimal validation
        if not name.strip():
            st.error("Name is required.")
        elif "@" not in email:
            st.error("Please enter a valid email address.")
        else:
            user.update({
                "name": name.strip(),
                "email": email.strip(),
                "license": license_no.strip(),
                "contact": contact.strip(),
                "specialties": [s for s in specialties if s],
                "bio": bio.strip(),
                "hours": pretty_hours,
                "hours_detail": new_hours,
                "preferences": {
                    "email_notifications": bool(email_notif),
                    "desktop_notifications": bool(desk_notif),
                    "show_patient_ids": bool(show_ids),
                },
            })
            save_user(user)
            st.success("Profile saved.")

st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

# ---------- security section (password & lock) ----------
st.markdown("#### Security")
sec1, sec2 = st.columns([2,1], gap="large")

with sec1:
    st.caption("Change password")
    cp1, cp2, cp3 = st.columns(3)
    current_pw = cp1.text_input("Current password", type="password")
    new_pw     = cp2.text_input("New password (min 6 chars)", type="password")
    confirm_pw = cp3.text_input("Confirm new password", type="password")

    if st.button("Update password"):
        if len(new_pw) < 6:
            st.error("New password must be at least 6 characters.")
        elif new_pw != confirm_pw:
            st.error("Passwords do not match.")
        elif current_pw != user.get("password",""):
            st.error("Current password is incorrect.")
        else:
            user["password"] = new_pw
            user["failed"] = 0
            user["locked"] = False
            save_user(user)
            st.success("Password updated.")

with sec2:
    st.caption("Account status")
    locked = bool(user.get("locked", False))
    st.write(f"Login status: {'🔒 Locked' if locked else '✅ Active'}")
    if locked:
        if st.button("Unlock account"):
            IdentityService(repo).reset_lock(me)
            st.success("Account unlocked."); st.rerun()

st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

# ---------- read-only preview ----------
st.markdown("#### Public snippet (how others may see you internally)")
st.markdown(
    f"""
    <div class='k-card'>
      <b>{user.get('name','')}</b><br/>
      License: {user.get('license','—')}<br/>
      Specialties: {', '.join(user.get('specialties', [])) or '—'}<br/>
      Hours: {user.get('hours','—')}<br/>
      Contact: {user.get('contact','—')}<br/>
      <span class='muted'>{user.get('bio','')}</span>
    </div>
    """,
    unsafe_allow_html=True
)
