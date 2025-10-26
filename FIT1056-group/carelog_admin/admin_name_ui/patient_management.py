# admin_name_ui/patient_management.py
from __future__ import annotations

from typing import Dict, Any, List
import streamlit as st
import pandas as pd
from datetime import date

from admin_name_utils.storage import (
    load_db, save_db,
    load_patients_file, save_patients_file, patients_file_to_app_list, patients_file_path
)

# ---------- UI helpers ----------
def _card_header(title: str, emoji: str = ""):
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:10px;">
               <div style="font-size:20px">{emoji}</div>
               <h4 style="margin:0;">{title}</h4>
           </div>""",
        unsafe_allow_html=True,
    )

def _kpi(label: str, value: str):
    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
            padding:10px 14px;border:1px solid rgba(255,255,255,.1);border-radius:14px;
            background:rgba(255,255,255,.03);">
            <div style="opacity:.9">{label}</div>
            <div style="font-weight:700">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _validate(rec: Dict[str, Any]) -> List[str]:
    errs = []
    if not (rec.get("id") or "").strip():
        errs.append("ID is required (e.g., P000011).")
    if not (rec.get("name") or "").strip():
        errs.append("Name is required.")
    if not (rec.get("dob") or "").strip():
        errs.append("Date of birth is required (YYYY-MM-DD).")
    else:
        try:
            _ = date.fromisoformat(str(rec["dob"]))
        except Exception:
            errs.append("DOB must be in ISO format (YYYY-MM-DD).")
    if not (rec.get("gender") or "").strip():
        errs.append("Gender is required.")
    return errs

def _next_patient_code(existing_keys: List[str]) -> str:
    nums = []
    for k in existing_keys:
        if isinstance(k, str) and k.upper().startswith("P"):
            try:
                nums.append(int(k[1:]))
            except Exception:
                pass
    nxt = (max(nums) + 1) if nums else 1
    return f"P{nxt:06d}"

# ---------- Page ----------
def render():
    st.session_state.setdefault("pm_selected_key", "")
    st.session_state.setdefault("pm_mode", "view")  # view | create

    file_path = patients_file_path().as_posix()
    st.markdown(
        "<h3 style='display:flex;align-items:center;gap:10px;margin:0 0 6px 0;'>"
        "👤 <span>Patient Management</span></h3>"
        f"<p style='margin:0;opacity:.8;'>Linked to <code>{file_path}</code> (singular).</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # Diagnostics banner (so you can confirm the file in use)
    st.info(f"Reading from: **{file_path}**")

    # Load strict file
    raw = load_patients_file()  # dict keyed by P000001 -> {...}
    if not isinstance(raw, dict):
        raw = {}
    keys_sorted = sorted(raw.keys(), key=lambda k: (len(k), k))

    st.caption(f"Loaded records: **{len(raw)}**  •  First keys: "
               f"{', '.join(list(raw.keys())[:5]) or '—'}")

    # KPIs
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1: _kpi("Total", str(len(raw)))
        with c2: _kpi("With MRN", str(sum(1 for v in raw.values() if v.get("mrn"))))
        with c3: _kpi("Visible to non-primary", str(sum(1 for v in raw.values() if v.get("visible_to_non_primary"))))

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Toolbar
    t1, t2, t3 = st.columns([1, 1, 1])
    with t1:
        if st.button("🔄 Reload file", use_container_width=True):
            st.session_state["pm_mode"] = "view"
            st.session_state["pm_selected_key"] = ""
            st.rerun()
    with t2:
        if st.button("💾 Save file", use_container_width=True):
            try:
                save_patients_file(raw)
                db = load_db()
                db["patients"] = patients_file_to_app_list(raw)
                save_db(db)
                st.success("Saved to data/patient.json and mirrored to internal DB.")
            except Exception as e:
                st.error(f"Could not write to data/patient.json: {e}")
    with t3:
        if st.button("➕ New patient", type="primary", use_container_width=True):
            st.session_state["pm_mode"] = "create"
            st.session_state["pm_selected_key"] = ""
            st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    mode = st.session_state["pm_mode"]

    # Table + quick open
    if mode == "view":
        q = st.text_input("Search (ID / name / MRN)")
        def _match(k: str, v: Dict[str, Any]) -> bool:
            if not q: return True
            s = q.lower()
            hay = " ".join([k, v.get("name",""), v.get("mrn",""), v.get("gender","")]).lower()
            return s in hay

        filt = [(k, raw[k]) for k in keys_sorted if _match(k, raw[k])]

        if filt:
            rows = [{
                "ID": k,
                "Name": v.get("name",""),
                "DOB": v.get("dob",""),
                "Gender": v.get("gender",""),
                "MRN": v.get("mrn",""),
                "Phone": v.get("emergency_contact",""),
            } for k, v in filt]
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            labels = [f"{r['ID']} — {r['Name']} ({r['DOB']})" for _, r in df.iterrows()]
            key_map = [r["ID"] for _, r in df.iterrows()]
            default_idx = 0
            if st.session_state["pm_selected_key"] in key_map:
                default_idx = key_map.index(st.session_state["pm_selected_key"])
            pick = st.selectbox("Open patient", list(range(len(labels))),
                                format_func=lambda i: labels[i], index=default_idx if labels else 0)
            if labels:
                st.session_state["pm_selected_key"] = key_map[pick]
        else:
            st.info("No matches.")

        sel_key = st.session_state.get("pm_selected_key") or ""
        sel = raw.get(sel_key) if sel_key else None

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if not sel:
            st.info("Select a patient above, or click “New patient”.")
            return

        _card_header(f"Details — {sel_key}", "🧾")

        tabs = st.tabs(["Profile", "Preferences", "Danger Zone"])

        with tabs[0]:
            with st.form("pm_edit"):
                st.text_input("ID", value=sel.get("id",""), disabled=True)
                name = st.text_input("Full name", value=sel.get("name",""))
                dob = st.text_input("DOB (YYYY-MM-DD)", value=sel.get("dob",""))
                gender = st.selectbox("Gender", ["Male","Female","Other"],
                                      index=(["Male","Female","Other"].index(sel.get("gender","Male"))
                                             if sel.get("gender") in ["Male","Female","Other"] else 0))
                mrn = st.text_input("MRN", value=sel.get("mrn",""))
                medical = st.text_area("Medical details", value=sel.get("medical_details",""), height=100)
                phone = st.text_input("Emergency contact", value=sel.get("emergency_contact",""))
                avatar = st.text_input("Avatar path", value=sel.get("avatar_path",""))
                submitted = st.form_submit_button("Save changes", type="primary")

            if submitted:
                rec = {
                    **sel,
                    "name": name.strip(),
                    "dob": dob.strip(),
                    "gender": gender.strip(),
                    "mrn": mrn.strip(),
                    "medical_details": medical.strip(),
                    "emergency_contact": phone.strip(),
                    "avatar_path": avatar.strip(),
                }
                errs = _validate(rec)
                if errs:
                    for e in errs: st.error(e)
                else:
                    raw[sel_key] = rec
                    try:
                        save_patients_file(raw)
                        db = load_db()
                        db["patients"] = patients_file_to_app_list(raw)
                        save_db(db)
                        st.success("Saved.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not write to data/patient.json: {e}")

        with tabs[1]:
            with st.form("pm_prefs"):
                pref_food = st.text_input("Preference: Food", value=sel.get("pref_food",""))
                pref_lang = st.text_input("Preference: Language", value=sel.get("pref_language",""))
                pref_nurse = st.text_input("Preference: Nurse gender", value=sel.get("pref_nurse_gender",""))
                vis = st.checkbox("Visible to non-primary providers", value=bool(sel.get("visible_to_non_primary", False)))
                submitted = st.form_submit_button("Save preferences", type="primary")
            if submitted:
                sel["pref_food"] = pref_food.strip()
                sel["pref_language"] = pref_lang.strip()
                sel["pref_nurse_gender"] = pref_nurse.strip()
                sel["visible_to_non_primary"] = bool(vis)
                raw[sel_key] = sel
                try:
                    save_patients_file(raw)
                    db = load_db()
                    db["patients"] = patients_file_to_app_list(raw)
                    save_db(db)
                    st.success("Preferences saved.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not write to data/patient.json: {e}")

        with tabs[2]:
            st.warning("Deleting a patient will remove them from data/patient.json. This cannot be undone.")
            confirm = st.text_input("Type the patient ID to confirm", placeholder=sel_key)
            if st.button("Delete patient", type="primary", disabled=(confirm.strip() != sel_key)):
                raw.pop(sel_key, None)
                try:
                    save_patients_file(raw)
                    db = load_db()
                    db["patients"] = patients_file_to_app_list(raw)
                    save_db(db)
                    st.success("Patient deleted.")
                    st.session_state["pm_selected_key"] = ""
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not write to data/patient.json: {e}")
        return

    # --------- Create mode ----------
    _card_header("Create patient (writes exact JSON format to data/patient.json)", "➕")
    with st.form("pm_create"):
        new_id = st.text_input("ID", value=_next_patient_code(keys_sorted), help="Format: P000001")
        name = st.text_input("Full name")
        dob = st.text_input("DOB (YYYY-MM-DD)")
        gender = st.selectbox("Gender", ["Male","Female","Other"])
        mrn = st.text_input("MRN")
        medical = st.text_area("Medical details", height=100)
        phone = st.text_input("Emergency contact")
        avatar = st.text_input("Avatar path", value="")
        pref_food = st.text_input("Preference: Food", value="")
        pref_lang = st.text_input("Preference: Language", value="")
        pref_nurse = st.text_input("Preference: Nurse gender", value="")
        vis = st.checkbox("Visible to non-primary providers", value=False)
        submitted = st.form_submit_button("Create", type="primary")

    if submitted:
        rec = {
            "id": new_id.strip(),
            "name": name.strip(),
            "dob": dob.strip(),
            "gender": gender.strip(),
            "mrn": mrn.strip(),
            "medical_details": medical.strip(),
            "emergency_contact": phone.strip(),
            "avatar_path": avatar.strip(),
            "pref_food": pref_food.strip(),
            "pref_language": pref_lang.strip(),
            "pref_nurse_gender": pref_nurse.strip(),
            "visible_to_non_primary": bool(vis),
        }
        errs = _validate(rec)
        if rec["id"] in raw:
            errs.append("A patient with this ID already exists.")
        if errs:
            for e in errs: st.error(e)
        else:
            raw[rec["id"]] = rec
            try:
                save_patients_file(raw)
                db = load_db()
                db["patients"] = patients_file_to_app_list(raw)
                save_db(db)
                st.success(f"Created {rec['id']} – {rec['name']}.")
                st.session_state["pm_selected_key"] = rec["id"]
                st.session_state["pm_mode"] = "view"
                st.rerun()
            except Exception as e:
                st.error(f"Could not write to data/patient.json: {e}")
