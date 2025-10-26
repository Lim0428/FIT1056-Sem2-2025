# carelog_nurse/pages/1_🧑‍🤝‍🧑_Patients.py
from __future__ import annotations
import json, html
from pathlib import Path
from datetime import date
import streamlit as st
from streamlit.components.v1 import html as st_html

from components.ui import apply_theme, page_header
from app.data_adapter import DataAdapter  # reads from /data/*.json

# ------------------- high-contrast page CSS -------------------
def _page_css():
    st.markdown("""
    <style>
      .panel { background:#0f1a2b; border:1px solid #1e3350; border-radius:18px; padding:16px; }
      .panel h3 { margin:0 0 10px 0; font-size:16px; font-weight:900; color:#eaf2ff; }
      .filters { background:#0f1a2b; border:1px solid #1e3350; border-radius:16px; padding:12px 14px; margin-bottom:10px; }

      /* Detail cards */
      .p-card { position:relative; background:#0e1726; border:1px solid #213651; border-radius:16px; padding:14px 16px; margin-bottom:12px; box-shadow:0 6px 20px rgba(0,0,0,.25); }
      .p-card.high:before, .p-card.medium:before, .p-card.low:before { content:""; position:absolute; left:0; top:0; bottom:0; width:6px; border-radius:16px 0 0 16px; }
      .p-card.high:before   { background:linear-gradient(180deg,#ff6262,#ff3b3b); }
      .p-card.medium:before { background:linear-gradient(180deg,#ffd166,#ffb703); }
      .p-card.low:before    { background:linear-gradient(180deg,#2ec4b6,#21a299); }
      .p-head { display:flex; align-items:center; gap:12px; }
      .avatar { width:32px; height:32px; border-radius:999px; background:#22324a; display:inline-block; }
      .p-title { font-weight:900; color:#f5f9ff; font-size:16px; }
      .muted { color:#a9bed6; }
      .line { height:1px; background:#1a2c45; margin:8px 0; border-radius:999px; }
      .chip { display:inline-block; padding:3px 10px; border-radius:999px; background:#17263a; color:#d7e6fb; margin-right:6px; font-size:12px; }
    </style>
    """, unsafe_allow_html=True)

# ------------------- paths & helpers -------------------
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PATIENTS_PATH = DATA_DIR / "patients.json"
NURSES_PATH = DATA_DIR / "nurses.json"

def _safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except Exception:
            pass

def _age(dob: str | None) -> str:
    try:
        y, m, d = map(int, (dob or "").split("-"))
        b, t = date(y, m, d), date.today()
        return str(t.year - b.year - ((t.month, t.day) < (b.month, b.day)))
    except Exception:
        return "—"

def _get_assigned(p: dict) -> str:
    return p.get("assigned_to") or p.get("assigned_nurse_id") or p.get("assignee_id") or ""

def _get_allergies(p: dict) -> list[str]:
    return p.get("allergies") or p.get("alergies") or []

def _load_nurse_ids() -> list[str]:
    try:
        with NURSES_PATH.open("r", encoding="utf-8") as f:
            obj = json.load(f)
            if isinstance(obj, list):
                return [n.get("id","") for n in obj if n.get("id")]
            if isinstance(obj, dict) and isinstance(obj.get("nurses"), list):
                return [n.get("id","") for n in obj["nurses"] if n.get("id")]
    except Exception:
        pass
    return ["nurse_001"]

def _navigate(page_rel_path: str) -> None:
    try:
        st.switch_page(page_rel_path)
    except Exception:
        st.page_link(page_rel_path, label="Open →")

def esc(x) -> str:
    return html.escape("" if x is None else str(x))

def _risk_tag(level: str | None) -> tuple[str, str]:
    lvl = (level or "low").lower()
    label = "High" if lvl=="high" else "Medium" if lvl=="medium" else "Low"
    cls = "p-high" if lvl=="high" else "p-medium" if lvl=="medium" else "p-low"
    return f'<span class="pill {cls}">{label}</span>', lvl

# ---------- normalization helpers (support dict-or-list without changing JSON) ----------
def _patients_to_list(obj) -> list[dict]:
    """Return a list of patient dicts whether input is list or {id: patient} dict."""
    if isinstance(obj, dict):
        # Keep stable order by key
        return [obj[k] for k in sorted(obj.keys())]
    return list(obj or [])

def _update_patient_in_obj(store, pid: str, mutate: dict) -> object:
    """
    Update patient with ID 'pid' in either a dict store or a list store,
    applying keys in 'mutate' and return the mutated store.
    """
    if isinstance(store, dict):
        # Find matching key by id in values
        key = None
        for k, v in store.items():
            if (v.get("id") or v.get("patient_id")) == pid:
                key = k
                break
        if key is not None:
            store[key].update(mutate)
        return store
    # list
    idx = next((i for i, v in enumerate(store) if (v.get("id") or v.get("patient_id")) == pid), None)
    if idx is not None:
        store[idx].update(mutate)
    return store

# ------------------- page -------------------
st.set_page_config(page_title="Patients", page_icon="🧑‍🤝‍🧑", layout="wide")
apply_theme()
_page_css()
page_header("Patients", "Assigned to you", "🧑‍🤝‍🧑")

data = DataAdapter()
patients_raw = data.patients()           # can be list OR dict (as in your JSON)
patients_list = _patients_to_list(patients_raw)
nurse_ids = _load_nurse_ids()

# Normalize model for view
norm = []
for p in patients_list:
    pid = p.get("id") or p.get("patient_id") or ""
    nm = p.get("name") or p.get("full_name") or pid
    gender = p.get("gender") or "—"
    dob = p.get("dob")
    risk = (p.get("risk") or "low").lower()
    assigned = _get_assigned(p)
    alist = _get_allergies(p)
    norm.append({
        "__raw": p, "ID": pid, "Name": nm, "Gender": gender,
        "Age": _age(dob), "Risk": risk, "AllergiesList": alist,
        "Allergies": ", ".join(alist) if alist else "", "Assigned": assigned,
    })

# ------------------- filters -------------------
st.markdown('<div class="filters">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([2, 1, 1, 1.2])
with c1: q = st.text_input("Search", placeholder="Search name or ID…").strip().lower()
with c2: risk_filter = st.selectbox("Risk", ["All", "High", "Medium", "Low"], index=0)
with c3: only_assigned = st.checkbox("Only my patients", value=False)
with c4: sort_by = st.selectbox("Sort by", ["Name", "Risk", "Age", "ID"], index=0)
st.markdown('</div>', unsafe_allow_html=True)

# apply filters/sort
view = norm
if q:
    view = [r for r in view if q in r["Name"].lower() or q in r["ID"].lower()]
if risk_filter != "All":
    view = [r for r in view if r["Risk"] == risk_filter.lower()]
if only_assigned:
    view = [r for r in view if (r["Assigned"] or "").lower() in {"nurse_001", "n001"}]
if sort_by == "Risk":
    order = {"high": 0, "medium": 1, "low": 2}
    view = sorted(view, key=lambda r: order.get(r["Risk"], 3))
elif sort_by == "Age":
    def _to_int(s: str):
        try:
            return int(s)
        except Exception:
            return 999
    view = sorted(view, key=lambda r: _to_int(r["Age"]))
else:
    view = sorted(view, key=lambda r: r[sort_by])

# ------------------- directory (sandboxed HTML) -------------------
st.markdown('<div class="panel"><h3>Patient directory</h3>', unsafe_allow_html=True)

table_css = """
<style>
  body { margin:0; background:transparent; color:#eaf2ff; }
  .wrap { border:1px solid #1e3350; border-radius:14px; overflow:hidden; }
  table { width:100%; border-collapse:separate; border-spacing:0; background:#0e1726; }
  thead th {
    background:#122139; color:#dfeaff; font-weight:800; font-size:12px; text-transform:uppercase;
    letter-spacing:.04em; padding:10px 12px; border-bottom:1px solid #1e3350; text-align:left;
  }
  tbody td { padding:12px; font-size:14px; color:#eaf2ff; border-bottom:1px solid #172946; }
  tbody tr:nth-child(odd) { background:#0f1930; }
  tbody tr:hover { background:#142244; }
  .muted { color:#a9bed6; }
  .pill { display:inline-block; padding:2px 8px; border-radius:999px; font-weight:800; font-size:11px; }
  .p-high { background:#ff6b6b; color:#0b1320; }
  .p-medium { background:#ffd166; color:#0b1320; }
  .p-low { background:#27d6c3; color:#0b1320; }
  .chip { display:inline-block; padding:3px 10px; border-radius:999px; background:#17263a; color:#d7e6fb; margin-right:6px; font-size:12px; }
</style>
"""

thead = """
<div class="wrap">
<table>
  <thead>
    <tr>
      <th style="width:28%">Name</th>
      <th style="width:12%">ID</th>
      <th style="width:10%">Gender</th>
      <th style="width:10%">Age</th>
      <th style="width:15%">Risk</th>
      <th>Allergies</th>
      <th style="width:12%">Assigned</th>
    </tr>
  </thead>
  <tbody>
"""

rows_html = []
for r in view:
    pill_html, _ = _risk_tag(r["Risk"])
    chips = " ".join([f"<span class='chip'>{esc(a)}</span>" for a in r["AllergiesList"]]) or "<span class='muted'>None</span>"
    rows_html.append(f"""
      <tr>
        <td>{esc(r["Name"])}</td>
        <td class="muted">{esc(r["ID"])}</td>
        <td>{esc(r["Gender"])}</td>
        <td>{esc(r["Age"])}</td>
        <td>{pill_html}</td>
        <td>{chips}</td>
        <td class="muted">{esc(r["Assigned"]) or "—"}</td>
      </tr>
    """)

tbody = "\n".join(rows_html) + "</tbody></table></div>"
st_html(table_css + thead + tbody, height=min(440, 90 + 44*len(view)), scrolling=True)
st.markdown('</div>', unsafe_allow_html=True)

# ------------------- details cards + actions + edit -------------------
st.markdown("")
st.markdown('<div class="panel"><h3>Details</h3>', unsafe_allow_html=True)

if not view:
    st.info("No patients match your filters.")
else:
    for r in view:
        p = r["__raw"]
        pid, name = r["ID"], r["Name"]
        pill_html, risk_lvl = _risk_tag(r["Risk"])
        allergies_list = r["AllergiesList"]

        st.markdown(
            f"""
            <div class="p-card {risk_lvl}">
              <div class="p-head">
                <span class="avatar"></span>
                <div>
                  <div class="p-title">{esc(name)} {pill_html}</div>
                  <div class="muted">ID: <b>{esc(pid)}</b> · Gender: <b>{esc(r["Gender"])}</b> · Age: <b>{esc(r["Age"])}</b></div>
                </div>
              </div>
              <div class="line"></div>
              <div>Allergies:
                {" ".join([f"<span class='chip'>{esc(a)}</span>" for a in allergies_list]) if allergies_list else "<span class='muted'>None</span>"}
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Action buttons + edit
        cA, cB, cC, cD = st.columns([1.4, 1.6, 1.4, 6])
        with cA:
            if st.button("🩺 Vitals & Notes", key=f"vn_{pid}"):
                st.session_state["patient_focus"] = pid
                _navigate("pages/2_🩺_Vitals_&_Notes.py")
        with cB:
            if st.button("💊 Medication MAR", key=f"mar_{pid}"):
                st.session_state["patient_focus"] = pid
                _navigate("pages/3_💊_Medication_MAR.py")
        with cC:
            if st.button("🗓️ Appointments", key=f"ap_{pid}"):
                st.session_state["patient_focus"] = pid
                _navigate("pages/4_🗓️_Appointments.py")
        with cD:
            with st.expander("▸ Edit / Raw JSON", expanded=False):
                e1, e2, e3 = st.columns([1.1, 1.4, 3])
                risk_val = e1.selectbox(
                    "Risk", ["low", "medium", "high"],
                    index=["low","medium","high"].index(r["Risk"]),
                    key=f"risk_{pid}"
                )
                nurses = _load_nurse_ids()
                assigned_val = e2.selectbox(
                    "Assigned Nurse", nurses + ["(none)"],
                    index=(nurses + ["(none)"]).index(r["Assigned"]) if r["Assigned"] in nurses else len(nurses),
                    key=f"ass_{pid}"
                )
                allergies_txt = e3.text_input(
                    "Allergies (comma-separated)", r["Allergies"],
                    key=f"all_{pid}"
                )

                colS, _ = st.columns([1, 3])
                if colS.button("💾 Save", key=f"save_{pid}"):
                    latest = data.patients()  # may be dict or list
                    # Build mutation dict from UI
                    mutate = {"risk": risk_val}
                    if isinstance(latest, dict):
                        # Update assigned field preserving original shape
                        # (assigned_to or assigned_nurse_id)
                        # First find the actual record
                        key = next((k for k,v in latest.items()
                                    if (v.get("id") or v.get("patient_id")) == pid), None)
                        if key is not None:
                            if "assigned_to" in latest[key]:
                                latest[key]["assigned_to"] = (None if assigned_val == "(none)" else assigned_val)
                            else:
                                latest[key]["assigned_nurse_id"] = (None if assigned_val == "(none)" else assigned_val)
                            alist = [a.strip() for a in allergies_txt.split(",") if a.strip()]
                            if "allergies" in latest[key]:
                                latest[key]["allergies"] = alist
                            else:
                                latest[key]["alergies"] = alist
                            latest[key]["risk"] = risk_val
                    else:
                        # list store
                        idx = next((i for i, pp in enumerate(latest)
                                    if (pp.get("id") or pp.get("patient_id")) == pid), None)
                        if idx is not None:
                            if "assigned_to" in latest[idx]:
                                latest[idx]["assigned_to"] = (None if assigned_val == "(none)" else assigned_val)
                            else:
                                latest[idx]["assigned_nurse_id"] = (None if assigned_val == "(none)" else assigned_val)
                            alist = [a.strip() for a in allergies_txt.split(",") if a.strip()]
                            if "allergies" in latest[idx]:
                                latest[idx]["allergies"] = alist
                            else:
                                latest[idx]["alergies"] = alist
                            latest[idx]["risk"] = risk_val

                    with PATIENTS_PATH.open("w", encoding="utf-8") as f:
                        json.dump(latest, f, indent=2, ensure_ascii=False)
                    st.success("Saved.")
                    _safe_rerun()

                st.caption("Raw record")
                st.json(p)

st.markdown("</div>", unsafe_allow_html=True)
