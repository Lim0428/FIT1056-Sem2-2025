# doctor_name_app/theme.py
from __future__ import annotations
import streamlit as st

# ---- Design tokens ----
PRIMARY  = "#2E5AAC"   # brand blue
ACCENT   = "#30C48D"   # success green
DANGER   = "#E55353"   # error red
BORDER   = "#334155"   # slate border on dark
FIELD_BG = "#0D1422"   # input background
TEXT     = "#E6E6E6"   # main text
PLACE    = "#94A3B8"   # placeholder text


def inject_theme() -> None:
    """Global CSS for dark UI, no white header, and correct sidebar button sizing."""
    st.markdown(
        f"""
<style>
/* ================== REMOVE TOP WHITE BAR / HEADER ================== */
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
div[data-testid="stStatusWidget"],
#stDecoration, .st-emotion-cache-1dp5vir, .stMainHeader {{
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  box-shadow: none !important;
  border: 0 !important;
}}

/* Pull content up a bit since header is gone */
section.main > div.block-container {{
  padding-top: .75rem !important;
  padding-bottom: 2rem !important;
}}

/* ================== APP SHELL ================== */
.stApp {{
  background: linear-gradient(180deg, #0F172A 0%, #0B1220 100%) !important;
  color: {TEXT} !important;
}}
.muted {{ color: #9AA4B2 !important; }}

/* ================== FIELDS ================== */
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
.stApp input::placeholder, .stApp textarea::placeholder {{
  color: {PLACE} !important; opacity: 1 !important;
}}
.stApp input:focus, .stApp textarea:focus {{
  outline: none !important;
  border-color: {PRIMARY} !important;
  box-shadow: 0 0 0 3px rgba(46,90,172,.35) !important;
}}
.stApp input[aria-invalid="true"], .stApp textarea[aria-invalid="true"] {{
  border-color: {DANGER} !important;
  box-shadow: 0 0 0 3px rgba(229,83,83,.28) !important;
}}

/* Selects (BaseWeb) */
div[data-baseweb="select"] > div {{
  background: {FIELD_BG} !important;
  border: 1px solid {BORDER} !important;
  border-radius: 10px !important;
}}
div[data-baseweb="select"] input {{ color: {TEXT} !important; }}
div[data-baseweb="select"] div[role="listbox"] {{ background: #0F172A !important; }}
div[data-baseweb="select"] div[role="option"] {{ color: {TEXT} !important; }}

/* Date/Time */
.stDateInput input, .stTimeInput input {{
  background: {FIELD_BG} !important;
  color: {TEXT} !important;
  border: 1px solid {BORDER} !important;
  border-radius: 10px !important;
}}

/* File uploader (dropzone + 'Browse files' pill) */
.stFileUploader > section {{
  background: {FIELD_BG} !important;
  border: 1px dashed {BORDER} !important;
  border-radius: 12px !important;
  color: {TEXT} !important;
}}
.stFileUploader [data-testid="stFileUploaderDropzone"] * {{
  color: {TEXT} !important;
}}
.stFileUploader [data-testid="stFileUploaderBrowseButton"],
.stFileUploader button[title="Browse files"] {{
  background: #F35454 !important;
  color: #FFFFFF !important;
  border: 1px solid #F35454 !important;
  border-radius: 10px !important;
  box-shadow: 0 4px 12px rgba(243,84,84,.25) !important;
}}
.stFileUploader [data-testid="stFileUploaderBrowseButton"]:hover,
.stFileUploader button[title="Browse files"]:hover {{
  filter: brightness(1.05) !important;
}}

/* Labels & text */
.stApp label, .stApp .stMarkdown p {{ color: {TEXT} !important; }}

/* ================== BUTTONS ================== */
/* Reset: do NOT globally force full width (this caused the giant Logout). */
.stButton > button, .stDownloadButton > button {{
  width: auto !important;
  background: {PRIMARY} !important;
  color: #fff !important;
  border: 1px solid {PRIMARY} !important;
  border-radius: 12px !important;
  padding: 10px 14px !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 14px rgba(46,90,172,.25) !important;
  transition: transform .02s ease-in-out, box-shadow .2s;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  filter: brightness(1.05) !important;
  box-shadow: 0 6px 18px rgba(46,90,172,.35) !important;
}}
.stButton > button:active, .stDownloadButton > button:active {{
  transform: translateY(1px) !important;
}}
/* Make buttons stretch only in MAIN content area */
section.main .stButton > button,
section.main .stDownloadButton > button {{
  width: 100% !important;
}}

/* Danger variant: wrap button with <div class="btn-danger"> */
.btn-danger > button {{
  background: {DANGER} !important; border-color: {DANGER} !important;
  box-shadow: 0 4px 14px rgba(229,83,83,.25) !important;
}}
.btn-danger > button:hover {{
  box-shadow: 0 6px 18px rgba(229,83,83,.35) !important;
}}

/* Radios/checkboxes accent */
.stApp [role="radio"] > div:has(input:checked),
.stApp input[type="checkbox"]:checked {{
  accent-color: {PRIMARY} !important;
}}

/* ================== SIDEBAR ================== */
section[data-testid="stSidebar"], div[data-testid="stSidebar"] {{
  background: #0D1320 !important;
}}
section[data-testid="stSidebar"] *, div[data-testid="stSidebar"] * {{
  color: {TEXT} !important;
}}
/* Slightly tighter padding (optional) */
section[data-testid="stSidebar"] .block-container,
div[data-testid="stSidebar"] .block-container {{
  padding-left: 1rem !important;
  padding-right: 1rem !important;
}}
/* Sidebar button sizing: not oversized */
section[data-testid="stSidebar"] .stButton > button,
section[data-testid="stSidebar"] .stDownloadButton > button,
div[data-testid="stSidebar"] .stButton > button,
div[data-testid="stSidebar"] .stDownloadButton > button {{
  width: 92% !important;          /* narrower than sidebar column */
  max-width: 240px !important;    /* keep compact */
  margin: 8px auto 0 auto !important;
  display: block !important;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def force_text_white() -> None:
    """Keep headings/labels/metrics readable on dark backgrounds."""
    st.markdown(
        f"""
<style>
h1, h2, h3, h4, h5, h6,
.stMarkdown, .stMarkdown p,
[data-testid="stMetricValue"], [data-testid="stMetricLabel"],
label, .stCaption, .stText {{ color: {TEXT} !important; }}
</style>
        """,
        unsafe_allow_html=True,
    )
