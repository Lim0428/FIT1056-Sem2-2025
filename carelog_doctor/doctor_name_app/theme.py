# doctor_name_app/theme.py
import streamlit as st

# ---- Design tokens ----
PRIMARY  = "#2E5AAC"   # brand blue
ACCENT   = "#30C48D"   # success green
DANGER   = "#E55353"   # error red
BORDER   = "#334155"   # slate border on dark
FIELD_BG = "#0D1422"   # input background
TEXT     = "#E6E6E6"   # main text
PLACE    = "#94A3B8"   # placeholder text

def inject_theme():
    st.markdown(
        f"""
        <style>
          /* ===== App shell ===== */
          .stApp {{
            background: linear-gradient(180deg, #0F172A 0%, #0B1220 100%) !important;
            color: {TEXT} !important;
          }}
          section.main > div.block-container {{
            padding-top: 0.75rem !important;   /* tighter top spacing */
            padding-bottom: 2rem !important;
          }}

          /* Remove Streamlit's default header/toolbar (blank bar) */
          header[data-testid="stHeader"] {{
            background: transparent !important;
            box-shadow: none !important;
            border: 0 !important;
            height: 0 !important;
            min-height: 0 !important;
            padding: 0 !important;
          }}
          header[data-testid="stHeader"] * {{ display: none !important; }}
          /* Hide floating status badge (optional) */
          div[data-testid="stStatusWidget"] {{ display: none !important; }}

          /* ===== Utility styles ===== */
          .pill {{
            display:inline-block; padding:4px 10px; border-radius:999px;
            background:{ACCENT}22; color:{ACCENT}; font-size:12px; margin-left:8px;
          }}
          .metric-card {{
            background: rgba(255,255,255,0.06); border-radius: 16px; padding: 16px;
            border:1px solid rgba(255,255,255,0.10);
          }}
          .muted {{ color: #9AA4B2 !important; }}

          /* ===== Unified fields: inputs, textareas, selects, pickers, uploaders ===== */
          /* Raw inputs */
          .stApp input[type="text"],
          .stApp input[type="password"],
          .stApp input[type="email"],
          .stApp input[type="tel"],
          .stApp textarea {{
            background: {FIELD_BG} !important;
            color: {TEXT} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 10px !important;
            box-shadow: none !important;
          }}
          .stApp input::placeholder,
          .stApp textarea::placeholder {{
            color: {PLACE} !important; opacity: 1 !important;
          }}
          .stApp input:focus,
          .stApp textarea:focus {{
            outline: none !important;
            border-color: {PRIMARY} !important;
            box-shadow: 0 0 0 3px rgba(46,90,172,.35) !important;
          }}
          .stApp input[aria-invalid="true"],
          .stApp textarea[aria-invalid="true"] {{
            border-color: {DANGER} !important;
            box-shadow: 0 0 0 3px rgba(229,83,83,.28) !important;
          }}

          /* BaseWeb select (Streamlit selectbox/multiselect) */
          div[data-baseweb="select"] > div {{
            background: {FIELD_BG} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 10px !important;
          }}
          div[data-baseweb="select"] input {{ color: {TEXT} !important; }}
          div[data-baseweb="select"] div[role="listbox"] {{ background: #0F172A !important; }}
          div[data-baseweb="select"] div[role="option"] {{ color: {TEXT} !important; }}

          /* Date/Time inputs */
          .stDateInput input, .stTimeInput input {{
            background: {FIELD_BG} !important;
            color: {TEXT} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 10px !important;
          }}

          /* File uploader */
          .stFileUploader > section {{
            background: {FIELD_BG} !important;
            border: 1px dashed {BORDER} !important;
            border-radius: 12px !important;
            color: {TEXT} !important;
          }}

          /* Labels */
          .stApp label, .stApp .stMarkdown p {{ color: {TEXT} !important; }}

          /* ===== Unified buttons (all Streamlit buttons) ===== */
          .stButton > button, .stDownloadButton > button {{
            width: 100% !important;
            background: {PRIMARY} !important;
            color: #fff !important;
            border: 1px solid {PRIMARY} !important;
            border-radius: 12px !important;
            padding: 10px 14px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 14px rgba(46,90,172,.25) !important;
            transition: transform .02s ease-in-out, box-shadow .2s;
          }}
          .stButton > button:hover,
          .stDownloadButton > button:hover {{
            filter: brightness(1.05) !important;
            box-shadow: 0 6px 18px rgba(46,90,172,.35) !important;
          }}
          .stButton > button:active,
          .stDownloadButton > button:active {{
            transform: translateY(1px) !important;
          }}
          /* Danger variant: wrap in <div class="btn-danger"> ...button... </div> */
          .btn-danger > button {{
            background: {DANGER} !important; border-color: {DANGER} !important;
            box-shadow: 0 4px 14px rgba(229,83,83,.25) !important;
          }}
          .btn-danger > button:hover {{
            box-shadow: 0 6px 18px rgba(229,83,83,.35) !important;
          }}

          /* Radio/checkbox accent */
          .stApp [role="radio"] > div:has(input:checked),
          .stApp input[type="checkbox"]:checked {{
            accent-color: {PRIMARY} !important;
          }}

          /* Sidebar tweaks (optional) */
          section[data-testid="stSidebar"] {{ background: #0D1320 !important; }}
          section[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
