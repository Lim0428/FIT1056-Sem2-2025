# doctor_name_pages/profile.py
from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import streamlit as st
from PIL import Image

from doctor_name_services.auth import current_doctor
from doctor_name_services.data_store import FILES, UPLOAD_DIR, DataStore


# ------------------------- tiny JSON utils -------------------------
def _read_json(path: Path, default: Any):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: Path, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ------------------------- doctor helpers -------------------------
def _load_doctors() -> list[dict]:
    return _read_json(FILES["doctors"], [])


def _save_doctors(rows: list[dict]):
    _write_json(FILES["doctors"], rows)


def _get_me() -> dict:
    me = current_doctor() or {}
    me_id = me.get("id")
    for d in _load_doctors():
        if d.get("id") == me_id:
            return d
    # fallback so page still renders
    return {"id": me_id or "doc1", "email": me.get("email", "doc@example.com")}


def _update_me(changes: dict):
    me = current_doctor() or {}
    me_id = me.get("id")
    docs = _load_doctors()
    for i, d in enumerate(docs):
        if d.get("id") == me_id:
            d.update({k: v for k, v in changes.items() if v is not None})
            docs[i] = d
            break
    _save_doctors(docs)


# ------------------------- styles -------------------------
def _css():
    st.markdown(
        """
        <style>
          /* card */
          .profile-card {
            background: rgba(255,255,255,0.04);
            border:1px solid rgba(148,163,184,0.28);
            border-radius:16px; padding:18px;
          }

          /* header row: avatar (left) + meta (right) */
          .profile-header {
            display:flex; align-items:center; gap:16px;
          }

          /* circular avatar */
          .avatar-wrap {
            width:112px; height:112px; border-radius:50%;
            border:1px solid rgba(148,163,184,0.35);
            background:#0D1422;
            display:flex; align-items:center; justify-content:center;
            overflow:hidden; flex:0 0 112px;
          }
          .avatar-wrap img.avatar-img {
            width:100%; height:100%; object-fit:cover; display:block;
          }
          .avatar-initials {
            font-size:36px; color:#CDE9FF; font-weight:700;
          }

          /* name + specialty (at the right of avatar) */
          .profile-meta .name {
            font-size:22px; font-weight:800; color:#FFFFFF;
            line-height:1.15; margin-bottom:2px;
          }
          .profile-meta .spec {
            color:#E6F0FF; opacity:.9;
          }

          /* metric pills */
          .metric-pill {
            background:rgba(255,255,255,0.04);
            border:1px solid rgba(148,163,184,0.28);
            border-radius:12px; padding:10px; text-align:center;
          }
          .metric-pill .v { font-size:20px; font-weight:800; color:#FFFFFF; }
          .metric-pill .l { font-size:12px; color:#A9B7CC; }

          /* tabs: brighter selected */
          .stTabs [role="tab"] { color:#DCEBFF !important; font-weight:600; padding:8px 14px; }
          .stTabs [role="tab"][aria-selected="true"] {
              color:#FFFFFF !important; border-bottom:2px solid #ff5c5c !important;
              background:rgba(255,255,255,0.04);
          }

          /* dark uploader + uploaded file row */
          [data-testid="stFileUploaderDropzone"] {
              background:#0D1422 !important;
              border:1px solid rgba(148,163,184,.28) !important;
              border-radius:12px !important;
          }
          [data-testid="stFileUploaderDropzone"] * { color:#E6F0FF !important; }
          .stFileUploader .uploadedFile, .stFileUploader .uploadedFile * {
              background:#0D1422 !important; color:#E6F0FF !important;
              border-color: rgba(148,163,184,.28) !important;
          }

          /* save button look (white) */
          .uploader-actions .stButton>button{
              background:#FFFFFF !important;
              color:#0B1220 !important;
              border:1px solid rgba(148,163,184,.35) !important;
              border-radius:12px !important;
              padding:.6rem 1.1rem !important;
              box-shadow: 0 2px 8px rgba(0,0,0,.12) !important;
          }
          .uploader-actions .stButton>button:hover{
              background:#F5F7FB !important;
              border-color: rgba(148,163,184,.55) !important;
          }
          .uploader-actions .stButton>button:disabled{
              background:#F0F2F6 !important;
              color:#7B8799 !important;
              border:1px solid rgba(148,163,184,.25) !important;
              box-shadow:none !important;
              cursor:not-allowed !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _metric(value: str, label: str):
    st.markdown(
        f"""<div class="metric-pill"><div class="v">{value}</div><div class="l">{label}</div></div>""",
        unsafe_allow_html=True,
    )


# ------------------------- image helpers -------------------------
def _path_to_data_url(path_str: str) -> Optional[str]:
    """Read an image file and return a base64 data URL (so browsers always show it)."""
    try:
        p = Path(path_str)
        if not p.exists():
            return None
        with open(p, "rb") as f:
            b = f.read()
        b64 = base64.b64encode(b).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return None


def _save_avatar_from_upload(uploaded_file, doc_id: str) -> str | None:
    """
    Save avatar from file_uploader to /uploads as a square 512px JPEG.
    Uses single-click flow; returns saved path or None.
    """
    try:
        raw = uploaded_file.getvalue()
        if not raw:
            return None
        img = Image.open(BytesIO(raw)).convert("RGB")

        # center square crop
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side)).resize((512, 512))

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        out_path = (UPLOAD_DIR / f"avatar_{doc_id}.jpg").as_posix()
        img.save(out_path, format="JPEG", quality=92)
        return out_path
    except Exception as e:
        st.error(f"Failed to process avatar: {e}")
        return None


def _avatar_html(me: dict) -> str:
    """
    Build circular avatar markup:
      - If avatar exists, embed as base64 data URL (not file://) so it always loads
      - Else show initials.
    """
    avatar_path = me.get("avatar")
    if avatar_path:
        data_url = _path_to_data_url(avatar_path)
        if data_url:
            return f'<div class="avatar-wrap"><img class="avatar-img" src="{data_url}" alt="avatar"/></div>'
    initials = (me.get("name") or me.get("email", "?")).strip()[:2].upper()
    return f'<div class="avatar-wrap"><div class="avatar-initials">{initials}</div></div>'


# ------------------------- page -------------------------
def page_profile(store: Optional[DataStore] = None):
    """
    Profile/com-card:
      • Header row: circular avatar (left) + name & specialty on the RIGHT
      • Change photo expander directly under header
      • White 'Save new avatar' button + toast on success + rerun
      • Remaining tabs (Overview, Edit profile, Schedule, Security)
    """
    _css()
    st.markdown("### My Profile")

    me = _get_me()
    doc_id = me.get("id", "doc1")
    name = me.get("name") or me.get("email", "Doctor")
    specialty = me.get("specialty", "General Medicine")

    # stats
    avg_rating, n_ratings = (store.doctor_average_rating() if store else (0.0, 0))
    patient_count = (store.count_assigned_patients() if store else 0)

    left, right = st.columns([5, 7], gap="large")

    # ---------------- LEFT: card + header (avatar + meta) + uploader ----------------
    with left:
        with st.container(border=True):
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)

            # Header row: avatar + meta on the RIGHT (avatar via base64 data URL)
            avatar_html = _avatar_html(me)
            st.markdown(
                f"""
                <div class="profile-header">
                  {avatar_html}
                  <div class="profile-meta">
                    <div class="name">{name}</div>
                    <div class="spec">{specialty}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Small metrics row
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                _metric(f"{avg_rating or '—'}", f"Overall rating{' ('+str(n_ratings)+')' if n_ratings else ''}")
            with c2:
                _metric(str(patient_count), "Patients")

            # ---------- Change photo (directly below header) ----------
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            with st.expander("Change photo", expanded=False):
                st.caption("Upload a square image for best results.")
                up = st.file_uploader(
                    "Select image",
                    type=["jpg", "jpeg", "png"],
                    label_visibility="collapsed",
                    accept_multiple_files=False,
                    key="prof_avatar",
                )

                # Optional inline preview (doesn’t affect save logic)
                if up is not None:
                    try:
                        st.image(up, caption="Preview", width=140, use_column_width=False)
                    except Exception:
                        pass

                st.markdown('<div class="uploader-actions">', unsafe_allow_html=True)
                save_clicked = st.button("Save new avatar", key="btn_save_avatar", disabled=(up is None))
                st.markdown("</div>", unsafe_allow_html=True)
                st.caption("JPG/PNG up to ~10MB.")

                if save_clicked:
                    if up is None:
                        st.warning("Please choose an image first.")
                    else:
                        saved = _save_avatar_from_upload(up, doc_id)
                        if saved:
                            _update_me({"avatar": saved})
                            st.toast("Avatar updated ✅", icon="✅")
                            st.rerun()
                        else:
                            st.error("Could not save avatar. Please try a different image.")

            st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- RIGHT: tabs ----------------
    with right:
        tabs = st.tabs(["Overview", "Edit profile", "Schedule", "Security"])

        # Overview
        with tabs[0]:
            with st.container(border=True):
                st.markdown("**Contact**")
                st.write(me.get("contact", "—"))
                st.markdown("**Email**")
                st.write(me.get("email", "—"))
                st.markdown("**License No.**")
                st.write(me.get("license_no", "—"))
                st.markdown("**Qualifications**")
                st.write(me.get("qualifications", "—"))
                st.markdown("**Working Hours**")
                st.write(me.get("working_hours", "—"))
                st.markdown("**Bio**")
                st.write(me.get("bio", "—"))

        # Edit
        with tabs[1]:
            with st.form("edit_profile_form", clear_on_submit=False):
                st.caption("Update your public profile information.")
                c1, c2 = st.columns(2)
                with c1:
                    f_name = st.text_input("Full name", value=me.get("name", ""))
                    f_email = st.text_input("Email", value=me.get("email", ""))
                    f_contact = st.text_input("Contact", value=me.get("contact", ""))
                    f_specialty = st.text_input("Specialty", value=me.get("specialty", "General Medicine"))
                with c2:
                    f_qual = st.text_input("Qualifications", value=me.get("qualifications", ""))
                    f_license = st.text_input("License No.", value=me.get("license_no", ""))
                    f_hours = st.text_input("Working hours", value=me.get("working_hours", "Mon–Fri 9:00–17:00"))
                f_bio = st.text_area("Short bio", value=me.get("bio", ""), height=120)

                saved = st.form_submit_button("Save changes", use_container_width=True)
                if saved:
                    _update_me({
                        "name": f_name.strip(),
                        "email": f_email.strip(),
                        "contact": f_contact.strip(),
                        "specialty": f_specialty.strip(),
                        "qualifications": f_qual.strip(),
                        "license_no": f_license.strip(),
                        "working_hours": f_hours.strip(),
                        "bio": f_bio.strip(),
                    })
                    st.success("Profile updated.")
                    st.rerun()

        # Schedule
        with tabs[2]:
            with st.container(border=True):
                st.markdown("**Working Hours**")
                st.write(me.get("working_hours", "Mon–Fri 9:00–17:00"))
                st.caption("If your schedule changes, update it in Edit profile.")

        # Security
        with tabs[3]:
            with st.form("security_form"):
                st.caption("Update your security question/answer (used for recovery).")
                q = st.text_input("Security question", value=me.get("safety_q", ""))
                a = st.text_input("Security answer", value=me.get("safety_a", ""), type="password")
                ok = st.form_submit_button("Save security settings", use_container_width=True)
                if ok:
                    _update_me({"safety_q": q, "safety_a": a})
                    st.success("Security settings updated.")
