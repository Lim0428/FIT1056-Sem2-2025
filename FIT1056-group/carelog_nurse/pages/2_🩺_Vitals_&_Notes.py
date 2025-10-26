# carelog_nurse/pages/2_🩺_Vitals_&_Notes.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
import html as _html

from components.ui import apply_theme, page_header
from app.nurse_service import NurseService
from app.data_adapter import DataAdapter

# ---------- paths & helpers ----------
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
VITALS_PATH = DATA_DIR / "vitals.json"
NOTES_PATH  = DATA_DIR / "notes.json"

def _safe_rerun():
    try: st.rerun()
    except AttributeError:
        try: st.experimental_rerun()
        except Exception: pass

def _read_json(path: Path, default):
    try:
        if not path.exists() or path.stat().st_size == 0:
            return default
        with path.open("r", encoding="utf-8") as f:
            txt = f.read().strip()
            if txt in {"", "[]", "{}", "null"}: return default
            return json.loads(txt)
    except Exception:
        return default

def _write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def _add_vitals_fallback(pid: str, payload: dict):
    rows = _read_json(VITALS_PATH, [])
    if isinstance(rows, dict):
        rows = list(rows.values())
    rows.append(payload | {"patient_id": pid})
    _write_json(VITALS_PATH, rows)

def _add_note_fallback(pid: str, text: str, nurse_id: str = "nurse_001"):
    rows = _read_json(NOTES_PATH, [])
    if isinstance(rows, dict):
        rows = list(rows.values())
    rows.append({
        "patient_id": pid,
        "author": nurse_id,
        "text": text,
        "created_at": datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
    })
    _write_json(NOTES_PATH, rows)

def _list_vitals(pid: str):
    rows = _read_json(VITALS_PATH, [])
    if isinstance(rows, dict):
        rows = [rows[k] for k in sorted(rows.keys()) if isinstance(rows[k], dict)]
    return [r for r in rows if (r.get("patient_id") or r.get("pid")) == pid]

def _list_notes(pid: str):
    rows = _read_json(NOTES_PATH, [])
    if isinstance(rows, dict):
        rows = [rows[k] for k in sorted(rows.keys()) if isinstance(rows[k], dict)]
    return [r for r in rows if (r.get("patient_id") or r.get("pid")) == pid]

def _safe_name(p: dict) -> str:
    return p.get("name") or p.get("full_name") or p.get("Name") or p.get("id") or p.get("patient_id") or "Patient"

# ---------- page ----------
st.set_page_config(page_title="Vitals & Notes", page_icon="🩺", layout="wide")
apply_theme()

# Keep your dark/white design + add two small scroll containers
st.markdown("""
<style>
  :root {
    --bg:#0f1a2b; --ink:#ffffff; --sub:#e5eeff; --edge:#1e3350; --card:#0e1726;
    --input:#132236; --inputEdge:#274264;
  }
  html, body, div, span, p, li, strong, em, small, h1, h2, h3, h4, h5, h6 { color:var(--ink) !important; }
  label, .stMarkdown, [data-testid="stMarkdownContainer"] * { color:var(--ink) !important; }
  .stSelectbox label, .stNumberInput label, .stTextArea label, .stTextInput label { color:var(--ink) !important; }
  ::placeholder { color:#e0ecff !important; opacity:1; }

  .panel { background:var(--bg); border:1px solid var(--edge); border-radius:18px; padding:16px; }
  .panel h3 { margin:0 0 10px 0; font-size:16px; font-weight:900; color:var(--ink); }
  .hint  { color:var(--sub); font-size:12px; }

  input, textarea, select {
    background:var(--input) !important; color:var(--ink) !important;
    border:1px solid var(--inputEdge) !important; border-radius:10px !important;
  }
  textarea { min-height:120px; }

  [data-baseweb="select"] > div,
  [data-testid="stMultiSelect"] > div,
  [data-testid="stDateInput"] input,
  [data-testid="stTimeInput"] input,
  [data-testid="stTextArea"] textarea,
  [data-testid="stTextInput"] input,
  [data-testid="stNumberInput"] input {
    background:var(--input) !important; color:var(--ink) !important; border:1px solid var(--inputEdge) !important;
  }

  .stApp [data-baseweb="popover"] [data-baseweb="menu"],
  .stApp div[role="listbox"] {
    background:#0f1a2b !important; color:var(--ink) !important; border:1px solid var(--inputEdge) !important; border-radius:10px !important;
  }
  .stApp [data-baseweb="popover"] [role="option"],
  .stApp div[role="option"] { color:var(--ink) !important; background:transparent !important; }
  .stApp [data-baseweb="popover"] [role="option"]:hover,
  .stApp div[role="option"]:hover { background:#132a48 !important; color:var(--ink) !important; }
  .stApp [data-baseweb="popover"] [role="option"][aria-selected="true"],
  .stApp div[role="option"][aria-selected="true"] { background:#17365f !important; color:var(--ink) !important; }

  .btn-primary, .stButton>button {
    border:1px solid #5b8bda; background:#2a4f8a; color:#ffffff;
    padding:8px 14px; border-radius:10px; font-weight:800;
  }
  .btn-primary:hover, .stButton>button:hover { background:#3564b3; border-color:#7fb0ff; }
  .stButton > button { display:inline-flex !important; visibility:visible !important; opacity:1 !important; }

  [data-testid="stSlider"] .st-c9, [data-testid="stSlider"] .st-c6 { background:#1b2c44 !important; }
  [data-testid="stSlider"] .st-bx { background:#2e5fa1 !important; }
  [data-testid="stSlider"] .st-bu { background:#4c84d8 !important; }

  .chip { display:inline-block; padding:3px 10px; border-radius:999px; background:#17263a; color:#ffffff; margin-right:6px; font-size:12px; }
  .pill { display:inline-block; padding:2px 8px; border-radius:999px; font-weight:800; font-size:11px; }
  .ok  { background:#27d6c3; color:#0b1320; }
  .warn{ background:#ffd166; color:#0b1320; }
  .bad { background:#ff6b6b; color:#0b1320; }

  .note { background:var(--card); border:1px solid #213651; border-radius:12px; padding:12px; margin-bottom:10px; color:var(--ink) !important; }
  .note .meta { color:#e0ecff; font-size:12px; margin-bottom:6px; }

  table, thead, tbody, th, td, tr { color:var(--ink) !important; }
  thead tr th { background:#122139 !important; color:#ffffff !important; border-bottom:1px solid var(--edge) !important; }
  tbody tr td { background:#0f1930 !important; border-bottom:1px solid #172946 !important; }

  /* Scroll containers for vitals & notes (fits ~3 rows/notes) */
  .vitals-scroll, .notes-scroll {
    background: var(--card);
    border: 1px solid #213651;
    border-radius: 12px;
    padding: 8px;
    max-height: 220px;           /* ~3 rows visible */
    overflow-y: auto;
  }
  .vitals-scroll thead th { position: sticky; top: 0; z-index: 1; }
  .vitals-scroll::-webkit-scrollbar,
  .notes-scroll::-webkit-scrollbar { width: 8px; }
  .vitals-scroll::-webkit-scrollbar-thumb,
  .notes-scroll::-webkit-scrollbar-thumb { background:#2a3d5c; border-radius:8px; }
  .vitals-scroll::-webkit-scrollbar-track,
  .notes-scroll::-webkit-scrollbar-track { background: transparent; }
</style>
""", unsafe_allow_html=True)

page_header("Vitals & Notes", "Record observations and progress", "🩺")

svc = NurseService()
adapter = DataAdapter()

# Patients (same source as Patients subpage)
p_src = adapter.patients()
if not p_src and hasattr(svc, "list_patients"):
    p_src = svc.list_patients()

patients: list[dict] = []
if isinstance(p_src, dict):
    patients = [p_src[k] for k in sorted(p_src.keys()) if isinstance(p_src[k], dict)]
elif isinstance(p_src, list):
    patients = [p for p in p_src if isinstance(p, dict)]

pid_options, id_to_name = [], {}
for p in patients:
    pid = p.get("id") or p.get("patient_id")
    if not pid:
        continue
    nm = (p.get("name") or p.get("full_name") or p.get("Name") or pid)
    pid_options.append(pid)
    id_to_name[pid] = nm

focus_pid = st.session_state.get("patient_focus")
default_idx = pid_options.index(focus_pid) if (focus_pid in pid_options) else 0 if pid_options else 0

# -------- Left: entry form --------
left, right = st.columns([1.25, 1])

with left:
    st.markdown('<div class="panel"><h3>Record Vitals</h3>', unsafe_allow_html=True)

    if not pid_options:
        st.info("No patients found in data/patients.json")
        st.stop()

    pid = st.selectbox(
        "Patient",
        options=pid_options,
        index=default_idx,
        format_func=lambda i: id_to_name.get(i, i),
        key="vitals_pid"
    )

    # Inputs in a form so the submit always shows
    with st.form("save_vitals_form", clear_on_submit=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sys = st.number_input("BP (Systolic)", min_value=60, max_value=250, value=120, step=1, key="in_sys")
        with c2:
            dia = st.number_input("BP (Diastolic)", min_value=30, max_value=160, value=80, step=1, key="in_dia")
        with c3:
            hr = st.number_input("Heart Rate", min_value=20, max_value=240, value=78, step=1, key="in_hr")
        with c4:
            spo2 = st.number_input("SpO₂ (%)", min_value=50, max_value=100, value=98, step=1, key="in_spo2")

        c5, c6 = st.columns([2,1])
        with c5:
            temp = st.number_input("Temperature (°C)", min_value=30.0, max_value=45.0, value=36.8, step=0.1, format="%.1f", key="in_temp")
        with c6:
            pain = st.slider("Pain (0-10)", min_value=0, max_value=10, value=2, key="in_pain")

        note = st.text_area("Note (optional)", placeholder="Context, observations, interventions…", key="in_note")

        # Guardrails
        flags = []
        if not (80 <= sys <= 200): flags.append("Systolic")
        if not (40 <= dia <= 120): flags.append("Diastolic")
        if not (30 <= hr  <= 200): flags.append("Heart Rate")
        if not (34.0 <= float(f"{temp:.1f}") <= 41.0): flags.append("Temperature")
        if not (85 <= spo2 <= 100): flags.append("SpO₂")
        if flags:
            st.caption(f"⚠️ Outside typical range: {', '.join(flags)}")

        submit_vitals = st.form_submit_button("Save Vitals", type="primary")

    if submit_vitals:
        payload = {
            "id": f"v_{int(datetime.utcnow().timestamp())}",
            "taken_at": datetime.utcnow().replace(microsecond=0).isoformat()+"Z",
            "ts": datetime.utcnow().replace(microsecond=0).isoformat()+"Z",
            "bp": f"{int(sys)}/{int(dia)}",
            "systolic": int(sys),
            "diastolic": int(dia),
            "hr": int(hr),
            "temp_c": float(f"{temp:.1f}"),
            "temperature": float(f"{temp:.1f}"),
            "spo2": int(spo2),
            "pain": int(pain),
            "note": (note.strip() or None),
        }
        try:
            if hasattr(svc, "add_vitals"):
                try:
                    svc.add_vitals(pid, payload)
                except Exception:
                    pass
            _add_vitals_fallback(pid, payload)  # always mirror to file
            st.success(f"Vitals saved for {id_to_name.get(pid,pid)}.")
            _safe_rerun()
        except Exception as e:
            st.error(f"Could not save vitals: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Add Nursing Note
    st.markdown('<div class="panel" style="margin-top:14px;"><h3>Add Nursing Note</h3>', unsafe_allow_html=True)
    note_text = st.text_area("Note", key="nursing_note", height=140, placeholder="Shift note, progress, education, etc.")
    if st.button("Save Note", key="save_note"):
        if not note_text.strip():
            st.warning("Write something before saving.")
        else:
            try:
                nurse_id = st.session_state.get("current_nurse_id") or "nurse_001"
                if hasattr(svc, "add_note"):
                    svc.add_note(pid, note_text.strip())
                else:
                    _add_note_fallback(pid, note_text.strip(), nurse_id=nurse_id)
                st.success(f"Note saved for {id_to_name.get(pid,pid)}.")
                _safe_rerun()
            except Exception as e:
                st.error(f"Could not save note: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# -------- Right: recent history --------
with right:
    st.markdown('<div class="panel"><h3>Latest Vitals</h3>', unsafe_allow_html=True)

    # Merge service + file
    svc_rows = []
    try:
        if hasattr(svc, "list_vitals"):
            svc_rows = svc.list_vitals(pid) or []
    except Exception:
        svc_rows = []
    file_rows = _list_vitals(pid)

    vitals_rows = []
    for src in (svc_rows, file_rows):
        if isinstance(src, dict):
            vitals_rows.extend([src[k] for k in sorted(src.keys()) if isinstance(src[k], dict)])
        elif isinstance(src, list):
            vitals_rows.extend([x for x in src if isinstance(x, dict)])
    vitals_rows = [v for v in vitals_rows if (v.get("patient_id") or v.get("pid")) == pid]

    def _ts_of(v: dict) -> str:
        return v.get("taken_at") or v.get("ts") or v.get("time") or ""
    vitals_rows = sorted(vitals_rows, key=_ts_of, reverse=True)  # keep all, we'll scroll
    # Build compact table
    table = []
    if vitals_rows:
        def sev_pill(v):
            bad = []
            try:
                s = int(v.get("systolic") or (str(v.get("bp","")).split("/")[0]))
                d = int(v.get("diastolic") or (str(v.get("bp","")).split("/")[1]))
                if s >= 160 or d >= 100: bad.append("BP")
            except Exception: pass
            try:
                hr_val = int(v.get("hr") or v.get("heart_rate") or -1)
                if hr_val != -1 and (hr_val < 50 or hr_val > 110): bad.append("HR")
            except Exception: pass
            try:
                sp = int(v.get("spo2")) if v.get("spo2") is not None else None
                if sp is not None and sp < 92: bad.append("SpO₂")
            except Exception: pass
            try:
                tc = float(v.get("temp_c") or v.get("temperature") or -999)
                if tc != -999 and (tc < 35.5 or tc > 38.5): bad.append("Temp")
            except Exception: pass
            return f'<span class="pill bad">Alert: {", ".join(bad)}</span>' if bad else '<span class="pill ok">OK</span>'

        for v in vitals_rows:
            bp_txt = v.get("bp") or f"{v.get('systolic','')}/{v.get('diastolic','')}".strip("/")
            table.append({
                "Taken (UTC)": _ts_of(v),
                "BP": bp_txt,
                "HR": v.get("hr",""),
                "Temp (°C)": v.get("temp_c") or v.get("temperature",""),
                "SpO₂ %": v.get("spo2",""),
                "Pain": v.get("pain",""),
                "Status": sev_pill(v),
            })
        df = pd.DataFrame(table)
        html_tbl = df.to_html(escape=False, index=False)
        st.markdown(f'<div class="vitals-scroll">{html_tbl}</div>', unsafe_allow_html=True)
    else:
        st.info("No vitals recorded yet.")
    st.markdown('</div>', unsafe_allow_html=True)

   # Notes timeline (scroll box ~3 notes tall)
    st.markdown('<div class="panel" style="margin-top:14px;"><h3>Notes Timeline</h3>', unsafe_allow_html=True)
    try:
        notes_rows = svc.list_notes(pid) if hasattr(svc, "list_notes") else _list_notes(pid)
    except Exception:
        notes_rows = _list_notes(pid)

    notes_rows = [n for n in notes_rows if isinstance(n, dict)]
    notes_rows = sorted(notes_rows, key=lambda r: r.get("created_at","") or r.get("ts",""), reverse=True)

    if notes_rows:
        # Build single-line HTML per note (no leading spaces => no Markdown code block)
        items = []
        for n in notes_rows:
            meta = (n.get("created_at") or n.get("ts","")) + " · " + (n.get("author") or n.get("nurse_id","nurse"))
            body_raw = n.get("text") or n.get("note","") or ""
            body = _html.escape(body_raw).replace("\n", "<br>")
            items.append(f'<div class="note"><div class="meta">{meta}</div><div>{body}</div></div>')
        notes_html = "".join(items)
        st.markdown(f'<div class="notes-scroll">{notes_html}</div>', unsafe_allow_html=True)
    else:
        st.info("No notes yet.")
    st.markdown('</div>', unsafe_allow_html=True)
