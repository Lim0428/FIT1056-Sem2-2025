# pages/5_🗳️_Feedback.py
import streamlit as st
from components.ui import apply_theme, card, require_auth   # no page_header to avoid double header
from app.patient import PatientService

st.set_page_config(page_title="Feedback", page_icon="🗳️", layout="wide")
apply_theme()
require_auth()

# ---------- Luxe / colorful styling (UI only; logic unchanged) ----------
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

      /* HERO header */
      .fb-hero{
        margin-top:8px; margin-bottom:18px; padding:22px 26px; border-radius:20px;
        background:
          radial-gradient(100% 140% at 0% 0%, rgba(124,180,255,.35), transparent 60%),
          linear-gradient(135deg, #172947, #111B32 40%, #13203C);
        border:1px solid rgba(255,255,255,.14);
        box-shadow: 0 26px 60px rgba(0,0,0,.55);
      }
      .fb-hero h1{ margin:0; font-size:42px; font-weight:900; letter-spacing:.3px; color:#F8FBFF; }
      .fb-hero .sub{ color:#D7E4FF; opacity:.98; margin-top:6px; font-weight:600; }
      .fb-hero .bar{
        height:6px; width:100%; border-radius:999px; margin-top:14px;
        background: linear-gradient(90deg, var(--c-blue), var(--c-teal), var(--c-green),
                                    var(--c-yellow), var(--c-orange), var(--c-pink), var(--c-purple));
        box-shadow: 0 8px 24px rgba(124,180,255,.25);
      }

      /* Inputs */
      .stTextArea textarea{
        background: var(--field) !important; color:#EAF2FF !important;
        border:1px solid rgba(255,255,255,.20) !important;
      }
      [data-testid="stMultiSelect"] div[data-baseweb="select"] > div{
        background: var(--field) !important; border:1px solid rgba(255,255,255,.20) !important;
      }
      [data-testid="stMultiSelect"] div[data-baseweb="select"] *{ color:#EAF2FF !important; }
      div[data-baseweb="popover"] *{ color:#EAF2FF !important; }
      div[data-baseweb="popover"] div, div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li{ background: var(--panel) !important; }
      [role="listbox"]{ background:var(--panel) !important; border:1px solid var(--panel-border) !important; }
      [role="option"]{ color:#EAF2FF !important; }
      [role="option"]:hover{ background: var(--hover) !important; }
      [role="option"][aria-selected="true"]{ background: var(--selected) !important; }

      /* Star preview + mood */
      .star-preview{
        font-size: 30px; line-height: 1.1; letter-spacing: 3px; margin: 4px 0 10px 0;
        text-shadow: 0 0 10px rgba(251, 191, 36, .18);
      }
      .star-preview .on  { color: #F59E0B; }
      .star-preview .off { color: #9FB0C3; opacity:.55; }
      .mood{ font-weight:900; color:#EAF2FF; opacity:.95; }

      /* Glow bar */
      .glowbar{
        height:10px; border-radius:999px; overflow:hidden; background:rgba(255,255,255,.08);
        border:1px solid rgba(255,255,255,.16);
      }
      .glowbar > div{
        height:100%;
        background: linear-gradient(90deg, #F59E0B, #FB923C, #2DD4BF, #7CB4FF);
        box-shadow: 0 0 16px rgba(245,158,11,.45);
      }

      /* History pill */
      .hist{
        display:flex; align-items:center; gap:10px;
        padding:8px 12px; border-radius:12px;
        border:1px solid rgba(255,255,255,.14);
        background: rgba(255,255,255,.06);
      }
      .hist .ts{ font-weight:900; letter-spacing:.2px; color:#EAF2FF; }
      .hist .stars{ font-weight:900; color:#F59E0B; letter-spacing:1px; }
      .hist .text{ color:#D7E4FF; opacity:.95; }
    </style>
    """,
    unsafe_allow_html=True,
)

# HERO
st.markdown(
    """
    <div class="fb-hero">
      <h1>Feedback</h1>
      <div class="sub">Tell us how we are doing</div>
      <div class="bar"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

svc = PatientService()
pid = st.session_state["auth_user"]

# ---- Fancy star picker (segmented) ----
if "fb_rating" not in st.session_state:
    st.session_state.fb_rating = 5

def star_picker(label: str, key: str = "fb_rating", default: int = 5) -> int:
    # Use segmented control for crisp picking 1..5 (you used it in other pages)
    rating = st.segmented_control(
        label,
        options=[1,2,3,4,5],
        default=st.session_state.get(key, default),
        help="Tap to select a star rating"
    )
    st.session_state[key] = int(rating)

    # Live star preview + mood
    r = int(rating)
    on  = "★" * r
    off = "☆" * (5 - r)
    mood_map = {
        1: "😣 Very poor",
        2: "☹️ Poor",
        3: "😐 Okay",
        4: "🙂 Good",
        5: "🤩 Excellent",
    }
    st.markdown(f"<div class='star-preview'><span class='on'>{on}</span><span class='off'>{off}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='mood'>{mood_map.get(r, 'How was it?')}</div>", unsafe_allow_html=True)

    # Glow bar fill
    pct = int((r/5)*100)
    st.markdown(
    f"""<div class='glowbar'><div style='width:{pct}%;'></div></div>""",
    unsafe_allow_html=True,
)
    return r

# ---- Submit form (logic unchanged) ----
with card("Submit feedback"):
    rating = star_picker("Rating")
    # Quick tags (optional)
    tags = st.multiselect(
        "Quick tags (optional)",
        ["Friendly staff", "Clean environment", "Short wait", "Clear explanation", "Comfortable", "Great food", "Quiet", "Needs improvement"],
        default=[]
    )
    # Comment
    text = st.text_area("Comments", placeholder="Tell us what stood out. Details help us improve!")

    col_submit, col_reset = st.columns([1,1])
    with col_submit:
        if st.button("Submit", type="primary", use_container_width=True):
            final_text = text.strip()
            if tags:
                tag_str = " | Tags: " + ", ".join(tags)
                final_text = (final_text + tag_str).strip()
            svc.add_feedback(pid, {"rating": int(rating), "text": final_text})
            if rating >= 5:
                st.balloons()
            elif rating <= 2:
                st.snow()  # gentle effect for low score—signals we take it seriously
            st.success("Thank you! Your feedback has been submitted.")
    with col_reset:
        if st.button("Reset", use_container_width=True):
            st.session_state.fb_rating = 5

# ---- History (unchanged logic; nicer display) ----
with card("Your feedback history"):
    items = list(reversed(svc.get_feedback(pid)))
    if not items:
        st.info("No feedback yet.")
    else:
        for f in items:
            stars_on  = "★" * int(f.get("rating", 0))
            stars_off = "☆" * (5 - int(f.get("rating", 0)))
            ts = f.get("ts", "—")
            txt = (f.get("text") or "").strip()
            st.markdown(
                f"""
                <div class="hist">
                  <div class="ts">{ts}</div>
                  <div class="stars">{stars_on}{stars_off}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if txt:
                st.markdown(f"<div class='text' style='margin:6px 2px 10px 2px'>{txt}</div>", unsafe_allow_html=True)
