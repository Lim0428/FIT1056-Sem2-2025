# medical_staff/components/staff_shared.py
from __future__ import annotations
import os, base64, mimetypes
import streamlit as st
from app.medical_staff_service import MedicalStaffService

_svc = MedicalStaffService()

@st.cache_data(show_spinner=False)
def _b64_of_file(path: str) -> str | None:
    """Read a local file and return 'data:<mime>;base64,<...>' or None."""
    if not path:
        return None
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return None
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        # default to png if unknown
        mime = "image/png"
    try:
        with open(path, "rb") as f:
            b = f.read()
        return f"data:{mime};base64,{base64.b64encode(b).decode('ascii')}"
    except Exception:
        return None

def _avatar_or_placeholder(avatar_path: str | None, name: str) -> str:
    """
    Returns an HTML <img> tag with a base64 data URL so the image renders
    without needing a public static path. Falls back to an initial badge.
    """
    data_url = _b64_of_file(avatar_path or "")
    if data_url:
        return (
            f'<img src="{data_url}" '
            'style="width:40px;height:40px;border-radius:10px;object-fit:cover;'
            'border:1px solid var(--border);" />'
        )
    initial = (name or "?")[:1].upper()
    return (
        '<div style="width:40px;height:40px;border-radius:10px;display:flex;align-items:center;'
        'justify-content:center;background:rgba(124,180,255,.18);border:1px solid var(--border);'
        'font-weight:900;color:var(--text);">'
        f'{initial}</div>'
    )

def pick_staff_and_patient(key_prefix: str = "pick", only_my: bool = False):
    """
    Staff/Patient picker:
      - Staff ID input (for audit)
      - Search patients (ID/Name/MRN/Medical details; case-insensitive)
      - Shows avatar + medical_details preview (now renders actual image)
    Returns: (staff_id: str, selected_patient: dict | None)
    """
    # --- Staff ID ---
    staff_default = st.session_state.get("auth_user", "S001")
    staff_id = st.text_input("Staff ID (for audit)", value=staff_default, key=f"{key_prefix}_staff")

    # --- Search box ---
    q = st.text_input("Search patient (ID / Name / MRN / Details)", key=f"{key_prefix}_q")

    # Filter via service (honours 'only_my' using staff assignments)
    assigned_to = staff_id if only_my else None
    results = _svc.search_patients(q, assigned_to=assigned_to)

    if not results:
        st.info("No matching patients.")
        return staff_id, None

    # Labels for dropdown (selectbox can't render custom HTML)
    labels = [f"{p.get('name','(no name)')} — {p.get('id','')}" for p in results]
    idx = st.selectbox("Select patient", options=list(range(len(results))),
                       format_func=lambda i: labels[i], key=f"{key_prefix}_sel")
    selected = results[idx]
    st.session_state["auth_user"] = staff_id  # persist for other pages

    # Live preview (avatar + medical details)
    name = selected.get("name", "(no name)")
    pid  = selected.get("id", "")
    md   = selected.get("medical_details", "")
    av   = _avatar_or_placeholder(selected.get("avatar_path"), name)

    st.markdown(
        f"""
        <div style="display:flex;gap:12px;align-items:center;margin-top:8px;">
          {av}
          <div style="line-height:1.15;">
            <div style="font-weight:900;letter-spacing:.2px;">{name} — {pid}</div>
            <div style="opacity:.85;font-size:13px;">{md}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    return staff_id, selected
