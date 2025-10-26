# pages/2_📝_Daily_Survey.py
import streamlit as st
from components.ui import apply_theme, page_header, card, require_auth, divider
from app.patient import PatientService

st.set_page_config(page_title="Daily Survey", page_icon="📝", layout="wide")
apply_theme()
require_auth()

# ---------- Dashboard-style look & feel (UI only; no logic changes) ----------
st.markdown(
    """
    <style>
      :root{
        --bg:#0B1329; --bg2:#0A1124; --text:#F7FAFF; --muted:#CFE0FF;
        --c-blue:#7CB4FF; --c-teal:#2DD4BF; --c-green:#34D399; --c-pink:#EC4899;
        --c-orange:#FB923C; --c-purple:#A78BFA; --c-yellow:#FDE047;
        --field:#0F1A2E; --panel:#0D172B; --panel-border:rgba(255,255,255,.22);
        --hover:rgba(124,180,255,.18); --selected:rgba(124,180,255,.28);
      }
      [data-testid="stAppViewContainer"]{ background:var(--bg) !important; color:var(--text) !important; }
      section[data-testid="stSidebar"]{ background:var(--bg2) !important; color:var(--text) !important; }
      section[data-testid="stSidebar"] *{ color:var(--text) !important; }
      [data-testid="stAppViewContainer"] *{ color:var(--text) !important; }

      /* ---- HERO like Dashboard ---- */
      .ds-hero{
        margin-top:8px; margin-bottom:18px; padding:22px 26px;
        border-radius:20px;
        background:
          radial-gradient(100% 140% at 0% 0%, rgba(124,180,255,.35), transparent 60%),
          linear-gradient(135deg, #172947, #111B32 40%, #13203C);
        border:1px solid rgba(255,255,255,.14);
        box-shadow: 0 26px 60px rgba(0,0,0,.55);
        position:relative;
      }
      .ds-hero h1{
        margin:0; font-size:42px; font-weight:900; letter-spacing:.3px;
        color:#F8FBFF;
      }
      .ds-hero .sub{ color:#D7E4FF; opacity:.98; margin-top:6px; font-weight:600; }
      .ds-hero .bar{
        height:6px; width:100%; border-radius:999px; margin-top:14px;
        background: linear-gradient(90deg, var(--c-blue), var(--c-teal), var(--c-green), var(--c-yellow), var(--c-orange), var(--c-pink), var(--c-purple));
        box-shadow: 0 8px 24px rgba(124,180,255,.25);
      }

      /* Hide the slim default header band this page adds right under the hero (optional) */
      .stMarkdown:has(.ds-hero) + div [data-testid="stHorizontalBlock"] { display:none; }

      /* ---- Inputs: dark & crisp ---- */
      .stTextInput > div > div > input,
      .stTextArea textarea,
      .stNumberInput input,
      .stDateInput > div > input{
        background: var(--field) !important;
        color:#EAF2FF !important;
        border:1px solid rgba(255,255,255,.20) !important;
      }
      /* Selectbox */
      [data-testid="stSelectbox"] div[data-baseweb="select"] > div{
        background: var(--field) !important;
        border:1px solid rgba(255,255,255,.20) !important;
      }
      [data-testid="stSelectbox"] div[data-baseweb="select"] *{ color:#EAF2FF !important; }
      [data-testid="stSelectbox"] div[data-baseweb="select"] div[class*="placeholder"]{ color:#9FB0C3 !important; }
      [data-testid="stSelectbox"] svg{ color:#EAF2FF !important; fill:#EAF2FF !important; }
      /* Dropdown panel */
      div[data-baseweb="popover"] *{ color:#EAF2FF !important; }
      div[data-baseweb="popover"] div, div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li{ background: var(--panel) !important; }
      [role="listbox"]{ background:var(--panel) !important; border:1px solid var(--panel-border) !important; }
      [role="option"]{ color:#EAF2FF !important; }
      [role="option"]:hover{ background: var(--hover) !important; }
      [role="option"][aria-selected="true"]{ background: var(--selected) !important; }

      /* Slider thumb/track tweak for better contrast */
      .stSlider [role="slider"]{ outline:none !important; }
      .stSlider > div > div [data-baseweb="slider"]{ color:#EAF2FF !important; }

      /* ---- Section micro-heading ---- */
      .chip-dot{
        width:10px; height:20px; border-radius:4px;
        background: linear-gradient(180deg, var(--c-teal), var(--c-blue));
        box-shadow: 0 0 14px rgba(45,212,191,.45);
        display:inline-block; vertical-align:middle; margin-right:10px;
      }
      .mini-title{ font-weight:900; letter-spacing:.3px; display:flex; align-items:center; gap:10px; }

      /* ---- History Grid Cards ---- */
      .survey-grid{ display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; }
      @media (max-width: 1200px){ .survey-grid{ grid-template-columns: repeat(2, 1fr);} }
      @media (max-width: 760px){ .survey-grid{ grid-template-columns: 1fr; } }

      .sv-card{
        border-radius:14px; padding:12px 14px;
        border:1px solid rgba(255,255,255,.14);
        background:
          radial-gradient(120% 120% at 0% 0%, rgba(124,180,255,.30), transparent 60%),
          rgba(255,255,255,.06);
        box-shadow: 0 16px 34px rgba(0,0,0,.35);
      }
      .sv-head{ display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
      .sv-ts{ font-weight:900; letter-spacing:.3px; }
      .pill{ padding:2px 10px; border-radius:999px; font-size:11px; font-weight:800;
             border:1px solid rgba(255,255,255,.18); background:rgba(255,255,255,.10); }
      .pill.great{ background:linear-gradient(90deg, rgba(52,211,153,.28), rgba(45,212,191,.20)); border-color:rgba(52,211,153,.45);}
      .pill.good { background:linear-gradient(90deg, rgba(45,212,191,.25), rgba(124,180,255,.18)); border-color:rgba(124,180,255,.35);}
      .pill.okay { background:linear-gradient(90deg, rgba(124,180,255,.22), rgba(167,139,250,.18)); border-color:rgba(167,139,250,.35);}
      .pill.bad  { background:linear-gradient(90deg, rgba(251,146,60,.25), rgba(253,224,71,.18)); border-color:rgba(251,146,60,.45);}
      .pill.awful{ background:linear-gradient(90deg, rgba(236,72,153,.28), rgba(167,139,250,.20)); border-color:rgba(236,72,153,.45);}
      .sv-row{ display:flex; gap:12px; align-items:center; margin:6px 0; }
      .kv{ font-size:12px; opacity:.95; min-width:78px; color:#DDE9FF; }
      .val{ font-weight:900; }

      /* Rainbow divider */
      .ribbon{ height:6px; background:linear-gradient(90deg,var(--c-blue),var(--c-teal),var(--c-green),var(--c-yellow),var(--c-orange),var(--c-pink),var(--c-purple)); border-radius:999px; opacity:.9; margin:6px 0 14px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Custom hero (matches Dashboard)
st.markdown(
    """
    <div class="ds-hero">
      <h1>Daily Survey</h1>
      <div class="sub">Log how you’re feeling today</div>
      <div class="bar"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

svc = PatientService()
pid = st.session_state["auth_user"]

# ---------------- Composer ----------------
with card("New entry"):
    st.markdown("<div class='mini-title'><span class='chip-dot'></span>Today</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        mood = st.selectbox("Mood", ["", "Great", "Good", "Okay", "Bad", "Awful"], index=0)
    with c2:
        pain = st.slider("Pain (0 none → 10 worst)", 0, 10, 0)
    with c3:
        sleep = st.number_input("Sleep (hours)", min_value=0.0, max_value=24.0, step=0.5, value=0.0)

    col_meds, col_note = st.columns([1,3])
    with col_meds:
        meds = st.toggle("Took meds today", value=False)
    with col_note:
        note = st.text_area("Notes (optional)", placeholder="Anything else you'd like to add?")

    if st.button("➕ Save entry", type="primary", use_container_width=True):
        ok = svc.add_survey(pid, {"mood": mood, "pain": pain, "sleep": sleep, "meds": meds, "note": note})
        if ok:
            st.success("Saved ✓")
            st.rerun()
        else:
            st.error("Could not save your entry.")

divider()
st.markdown("<div class='ribbon'></div>", unsafe_allow_html=True)

# ---------------- History ----------------
with card("History"):
    items = svc.get_surveys(pid)
    if not items:
        st.caption("No survey entries yet.")
    else:
        def _pill_cls(m: str) -> str:
            m = (m or "").strip().lower()
            return {"great":"great","good":"good","okay":"okay","bad":"bad","awful":"awful"}.get(m,"")

        st.markdown("<div class='survey-grid'>", unsafe_allow_html=True)
        for s in items:
            ts = s.get("ts","—")
            mood = s.get("mood","—")
            pain = s.get("pain","—")
            sleep = s.get("sleep","—")
            meds = "Yes" if s.get("meds") else "No"
            note = s.get("note","—") or "—"
            cls = _pill_cls(mood)

            st.markdown(
                f"""
                <div class="sv-card">
                  <div class="sv-head">
                    <div class="sv-ts">{ts}</div>
                    <div class="pill {cls}">{mood if mood else '—'}</div>
                  </div>
                  <div class="sv-row"><div class="kv">Pain</div><div class="val">{pain}</div></div>
                  <div class="sv-row"><div class="kv">Sleep</div><div class="val">{sleep} h</div></div>
                  <div class="sv-row"><div class="kv">Meds</div><div class="val">{meds}</div></div>
                  <div class="sv-row"><div class="kv">Note</div><div class="val" style="font-weight:700; opacity:.95">{note}</div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
