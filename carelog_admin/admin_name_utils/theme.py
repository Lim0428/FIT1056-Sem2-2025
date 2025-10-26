# admin_name_utils/theme.py
import streamlit as st
from admin_name_utils.doctors_io import list_doctors, save_doctors, upsert_doctor, delete_doctor

def inject_theme():
    """Dark navy theme with safe CSS (no container hiding or absolute layouts)."""
    st.markdown("""
    <style>
      :root{
        --bg:#0f1b2d;
        --panel:#12213a;
        --muted:#97a6c1;
        --text:#e9eef7;
        --accent:#60a5fa;
        --accent-2:#34d399;
      }
      html, body, [data-testid="stAppViewContainer"]{
        background: var(--bg) !important;
        color: var(--text) !important;
      }
      /* Sidebar look only (do not hide/show with CSS) */
      [data-testid="stSidebar"]{
        background: linear-gradient(180deg, #101d33, #0f1b2d) !important;
        border-right: 1px solid rgba(255,255,255,.06);
      }
      /* Panels and expanders */
      .stMarkdown, .stContainer, .stDataFrame, .stMetric, .stAlert{
        color: var(--text) !important;
      }
      .stExpander{
        background: var(--panel) !important;
        border: 1px solid rgba(255,255,255,.08) !important;
        border-radius: 12px !important;
      }
      /* Buttons */
      .stButton>button{
        border-radius: 10px;
        font-weight: 600;
      }
      .stButton>button[kind="primary"], .stButton>button[data-baseweb="button"]{
        background: var(--accent) !important;
        color: #08111f !important;
        border: none !important;
      }
      /* Inputs */
      .stTextInput>div>div>input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"]{
        background: rgba(255,255,255,.06) !important;
        border: 1px solid rgba(255,255,255,.10) !important;
        color: var(--text) !important;
      }
    </style>
    """, unsafe_allow_html=True)
