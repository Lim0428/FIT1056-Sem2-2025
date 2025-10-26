# carelog_nurse/pages/3_💊_Medication_MAR.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
import streamlit as st
import pandas as pd

from components.ui import apply_theme, page_header
from app.data_adapter import DataAdapter

# ---------- paths ----------
ROOT = Path(__file__).resolve().parents[2]   # <repo root>
DATA_DIR = ROOT / "data"
MEDS_PATH = DATA_DIR / "medications.json"    # MAR store

# ---------- style ----------
st.set_page_config(page_title="Medication MAR", page_icon="💊", layout="wide")
apply_theme()
st.markdown("""
<style>
  .panel { background:#0f1a2b; border:1px solid #1e3350; border-radius:18px; padding:16px; }
  .panel h3 { margin:0 0 10px 0; font-size:16px; font-weight:900; color:#eaf2ff; }
  .muted { color:#9fb0c3; }
</style>
""", unsafe_allow_html=True)
page_header("Medication Administration Record (MAR)", "Record & review administrations", "💊")

# ---------- helpers ----------
def _load_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
            return obj if obj is not None else default
    except Exception:
        return default

def _as_list_of_dicts(obj) -> list[dict]:
    if isinstance(obj, dict):
        # In case someone stored {"items":[...]} etc.
        if isinstance(obj.get("items"), list):
            return [x for x in obj["items"] if isinstance(x, dict)]
        # Or a dict keyed by id
        return [obj[k] for k in sorted(obj.keys()) if isinstance(obj[k], dict)]
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    return []

def _now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _save_meds(rows: list[dict]):
    MEDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MEDS_PATH.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

def _next_id(rows: list[dict]) -> int:
    cur = 0
    for r in rows:
        try:
            cur = max(cur, int(r.get("id") or 0))
        except Exception:
            pass
    return cur + 1

# ---------- data ----------
data = DataAdapter()

# Patient list (same source as Patients subpage)
patients = data.patients()  # list[dict]
pid_to_name = {}
options = []
for p in patients:
    pid = p.get("id") or p.get("patient_id")
    nm  = p.get("name") or p.get("full_name") or pid or ""
    if not pid:
        continue
    pid_to_name[pid] = nm
    options.append(f"{pid} — {nm}")

# Decide default selection (use patient_focus if set)
default_pid = st.session_state.get("patient_focus") or None
default_label = None
if default_pid and default_pid in pid_to_name:
    default_label = f"{default_pid} — {pid_to_name[default_pid]}"

# ---------- layout ----------
left, right = st.columns([1.2, 1])

with left:
    st.markdown('<div class="panel"><h3>Patient</h3>', unsafe_allow_html=True)
    sel = st.selectbox(
        "Select patient",
        options=(options if options else ["— No patients —"]),
        index=(options.index(default_label) if (default_label and default_label in options) else 0) if options else 0,
        key="mar_patient_select",
    )
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel"><h3>Nurse</h3>', unsafe_allow_html=True)
    active_nurse = st.session_state.get("current_nurse_id") or "N001"
    st.text_input("Administering nurse (ID)", value=active_nurse, key="mar_nurse_id", disabled=False)
    st.caption("This should match your nurse identity; it will be stored with each administration.")
    st.markdown('</div>', unsafe_allow_html=True)

if not options:
    st.info("No patients available in data/patients.json.")
    st.stop()

# Extract selected patient_id
selected_pid = sel.split(" — ", 1)[0]
selected_name = pid_to_name.get(selected_pid, selected_pid)

# ---------- existing MAR entries for this patient ----------
all_meds = _as_list_of_dicts(_load_json(MEDS_PATH, []))
pat_meds = [m for m in all_meds if (m.get("patient_id") or m.get("pid")) == selected_pid]
pat_meds = sorted(pat_meds, key=lambda r: r.get("ts",""), reverse=True)

st.markdown('<div class="panel"><h3>Existing administrations</h3>', unsafe_allow_html=True)
if pat_meds:
    df = pd.DataFrame([
        {
            "When": (m.get("ts") or m.get("time") or "")[:16].replace("T", " "),
            "Drug": m.get("drug") or m.get("medication") or "",
            "Dose": m.get("dose") or "",
            "Route": m.get("route") or "",
            "Nurse": m.get("nurse_id") or m.get("by") or "",
            "Notes": m.get("notes") or m.get("remark") or "",
        }
        for m in pat_meds
    ])
    st.dataframe(df, use_container_width=True, hide_index=True, height=min(360, 44*(len(df)+1)))
else:
    st.caption("No administrations recorded yet.")

st.markdown('</div>', unsafe_allow_html=True)

# ---------- add new administration ----------
st.markdown('<div class="panel"><h3>Record administration</h3>', unsafe_allow_html=True)

with st.form("mar_form", clear_on_submit=True):
    c1, c2 = st.columns([1.2, 1])
    with c1:
        drug = st.text_input("Medication / drug", placeholder="e.g., Paracetamol")
        dose = st.text_input("Dose", placeholder="e.g., 500 mg")
        route = st.selectbox("Route", ["PO (Oral)", "IV", "IM", "SC", "SL", "Topical", "Inhalation", "PR", "Other"], index=0)
    with c2:
        when = st.text_input("Time (ISO)", value=_now_iso())
        prn = st.checkbox("PRN (as needed)")
        prn_reason = st.text_input("PRN reason (optional)", placeholder="e.g., pain ≥ 5/10") if prn else ""

    notes = st.text_area("Notes (optional)", height=80, placeholder="Additional context, site, double-check nurse, etc.")

    submitted = st.form_submit_button("Add to MAR")

if submitted:
    # Basic validation
    problems = []
    if not (drug or "").strip():
        problems.append("Medication/drug is required.")
    if not (dose or "").strip():
        problems.append("Dose is required.")
    if not (route or "").strip():
        problems.append("Route is required.")
    if problems:
        for p in problems:
            st.error(p)
    else:
        nurse_id = st.session_state.get("mar_nurse_id") or st.session_state.get("current_nurse_id") or "N001"
        entry = {
            "id": _next_id(all_meds),
            "patient_id": selected_pid,
            "ts": when.strip() or _now_iso(),
            "drug": drug.strip(),
            "dose": dose.strip(),
            "route": route.split(" ")[0],   # take short code
            "nurse_id": nurse_id,
            "notes": (notes or "").strip(),
            "status": "given",
        }
        if prn:
            entry["prn"] = True
            if prn_reason.strip():
                entry["prn_reason"] = prn_reason.strip()

        # append and save
        all_meds.append(entry)
        _save_meds(all_meds)
        st.success(f"Recorded {entry['drug']} ({entry['dose']}) via {entry['route']} for {selected_pid}.")
        st.experimental_rerun()

st.markdown('</div>', unsafe_allow_html=True)
