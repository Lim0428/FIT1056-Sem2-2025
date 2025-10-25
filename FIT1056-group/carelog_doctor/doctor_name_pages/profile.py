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
from doctor_name_services.data_store import FILES, UPLOAD_DIR
from doctor_name_services.data_store import DataStore  # for stats


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
          .profile-card {
            background: rgba(255,255,255,0.04);
            border:1px solid rgba(148,163,184,0.28);
            border-radius:16px; padding:16px;
          }
          .avatar-wrap {
            width:112px; height:112px; border-radius:50%;
            border:1px solid rgba(148,163,184,0.35);
            background:#0D1422; display:flex; align-items:center; justify-content:center;
            overflow:hidden;
          }
          .avatar-img { width:100%; height:100%; object-fit:cover; }
          .metric-pill {
            background:rgba(255,255,255,0.04);
            border:1px solid rgba(148,163,184,0.28);
            border-radius:12px; padding:10px; text-align:center;
          }
          .metric-pill .v { font-size:20px; font-weight:800; }
          .metric-pill .l { font-size:12px; color:#A9B7CC; }
          .thin-note { font-size:12px; color:#9FB1C8; }
          .uploader-wrap .stButton>button {
              background:transparent; color:#BFE9FF; border-width:1.5px;
              border-style:solid; border-image:linear-gradient(90deg,#4FC3F7,#2E5AAC) 1;
              border-radius:14px; padding:.45rem .9rem;
          }
          .uploader-wrap .stButton>button:hover { background:rgba(79,195,247,.08); }
          .stTabs [role="tab"] { color:#DCEBFF !important; font-weight:600; padding:8px 14px; }
          .stTabs [role="tab"][aria-selected="true"] {
              color:#FFFFFF !important; border-bottom:2px solid #ff5c5c !important;
              background:rgba(255,255,255,0.04);
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


# ------------------------- avatar render (base64) -------------------------
def _avatar_block(me: dict):
    """
    Show avatar reliably by embedding as data: URL (base64).
    This avoids 'file://...' which browsers cannot access inside Streamlit.
    """
    avatar_path = me.get("avatar")
    if avatar_path and Path(avatar_path).exists():
        try:
            with open(avatar_path, "rb") as f:
                raw = f.read()
            # best-effort mime sniff (default jpeg)
            suffix = Path(avatar_path).suffix.lower()
            mime = "image/png" if suffix == ".png" else "image/jpeg"
            b64 = base64.b64encode(raw).decode("ascii")
            st.markdown(
                f"""
                <div class="avatar-wrap">
                  <img class="avatar-img" src="data:{mime};base64,{b64}" />
                </div>
                """,
                unsafe_allow_html=True,
            )
            return
        except Exception:
            pass  # fall back to initials if anything goes wrong

    # fallback initials
    initials = (me.get("name") or me.get("email", "?")).strip()[:2].upper()
    st.markdown(
        f"""<div class="avatar-wrap" style="font-size:36px;color:#CDE9FF">{initials}</div>""",
        unsafe_allow_html=True,
    )


# ------------------------- avatar saving -------------------------
def _save_avatar_from_upload(uploaded_file, doc_id: str) -> Optional[str]:
    """
    Robust save using getvalue() to avoid zero-length reads.
    Always writes JPEG at uploads/avatar_<doc_id>.jpg.
    """
    try:
        raw = uploaded_file.getvalue()  # reliable across browsers
        img = Image.open(BytesIO(raw)).convert("RGB")
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        out_path = UPLOAD_DIR / f"avatar_{doc_id}.jpg"

        # Square center-crop + resize to keep the circle crisp
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side)).resize((512, 512))
        img.save(out_path, format="JPEG", quality=92)
        return out_path.as_posix()
    except Exception as e:
        st.error(f"Failed to process avatar: {e}")
        return None


# ------------------------- page -------------------------
def page_profile(store: Optional[DataStore] = None):
    _css()
    st.markdown("### My Profile")

    me_row = _get_me()
    doc_id = me_row.get("id", "doc1")
    name = me_row.get("name") or me_row.get("email", "Doctor")
    specialty = me_row.get("specialty", "General Medicine")

    # stats
    avg_rating, n_ratings = (store.doctor_average_rating() if store else (0.0, 0))
    patient_count = (store.count_assigned_patients() if store else 0)

    left, right = st.columns([5, 7], gap="large")

    # ---------------- LEFT: card + avatar + uploader ----------------
    with left:
        with st.container(border=True):
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)

            # avatar
            _avatar_block(me_row)
            st.markdown(
                f"<div style='font-size:22px;font-weight:800;margin-top:10px'>{name}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"<div style='opacity:.9'>{specialty}</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                _metric(
                    f"{avg_rating or '—'}",
                    f"Overall rating{' ('+str(n_ratings)+')' if n_ratings else ''}",
                )
            with c2:
                _metric(str(patient_count), "Patients")

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

            # compact, nice uploader directly under avatar
            with st.expander("Change photo", expanded=False):
                st.caption("Upload a square image for best results.")
                up = st.file_uploader(
                    "Select image",
                    type=["jpg", "jpeg", "png"],
                    key="prof_avatar",
                    label_visibility="collapsed",
                )
                if up is not None:
                    # inline preview
                    try:
                        st.image(up, caption="Preview", use_column_width=False, width=140)
                    except Exception:
                        pass

                    st.markdown('<div class="uploader-wrap">', unsafe_allow_html=True)
                    if st.button("Save new avatar", key="btn_save_avatar"):
                        saved = _save_avatar_from_upload(up, doc_id)
                        if saved:
                            _update_me({"avatar": saved})
                            st.toast("Avatar updated ✅", icon="✅")
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown('<div class="thin-note">JPG/PNG up to ~10MB.</div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- RIGHT: tabs ----------------
    with right:
        tabs = st.tabs(["Overview", "Edit profile", "Schedule", "Security"])

        # Overview
        with tabs[0]:
            with st.container(border=True):
                st.markdown("**Contact**")
                st.write(me_row.get("contact", "—"))
                st.markdown("**Email**")
                st.write(me_row.get("email", "—"))
                st.markdown("**License No.**")
                st.write(me_row.get("license_no", "—"))
                st.markdown("**Qualifications**")
                st.write(me_row.get("qualifications", "—"))
                st.markdown("**Working Hours**")
                st.write(me_row.get("working_hours", "—"))
                st.markdown("**Bio**")
                st.write(me_row.get("bio", "—"))

        # Edit
        with tabs[1]:
            with st.form("edit_profile_form", clear_on_submit=False):
                st.caption("Update your public profile information.")
                c1, c2 = st.columns(2)
                with c1:
                    f_name = st.text_input("Full name", value=me_row.get("name", ""))
                    f_email = st.text_input("Email", value=me_row.get("email", ""))
                    f_contact = st.text_input("Contact", value=me_row.get("contact", ""))
                    f_specialty = st.text_input(
                        "Specialty", value=me_row.get("specialty", "General Medicine")
                    )
                with c2:
                    f_qual = st.text_input(
                        "Qualifications", value=me_row.get("qualifications", "")
                    )
                    f_license = st.text_input("License No.", value=me_row.get("license_no", ""))
                    f_hours = st.text_input(
                        "Working hours", value=me_row.get("working_hours", "Mon–Fri 9:00–17:00")
                    )
                f_bio = st.text_area("Short bio", value=me_row.get("bio", ""), height=120)

                saved = st.form_submit_button("Save changes", use_container_width=True)
                if saved:
                    _update_me(
                        {
                            "name": f_name.strip(),
                            "email": f_email.strip(),
                            "contact": f_contact.strip(),
                            "specialty": f_specialty.strip(),
                            "qualifications": f_qual.strip(),
                            "license_no": f_license.strip(),
                            "working_hours": f_hours.strip(),
                            "bio": f_bio.strip(),
                        }
                    )
                    st.success("Profile updated.")
                    st.rerun()

        # Schedule (read-only helper)
        with tabs[2]:
            with st.container(border=True):
                st.markdown("**Working Hours**")
                st.write(me_row.get("working_hours", "Mon–Fri 9:00–17:00"))
                st.caption("If your schedule changes, update it in Edit profile.")

        # Security
        with tabs[3]:
            with st.form("security_form"):
                st.caption("Update your security question/answer (used for recovery).")
                q = st.text_input("Security question", value=me_row.get("safety_q", ""))
                a = st.text_input("Security answer", value=me_row.get("safety_a", ""), type="password")
                ok = st.form_submit_button("Save security settings", use_container_width=True)
                if ok:
                    _update_me({"safety_q": q, "safety_a": a})
                    st.success("Security settings updated.")
