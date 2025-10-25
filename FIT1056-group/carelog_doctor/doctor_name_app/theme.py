# doctor_name_app/theme.py
import streamlit as st

def inject_theme():
    st.markdown(
        """
        <style>
        :root{
          --bg:#0A0F18; --panel:#0B1220; --border:rgba(148,163,184,.28);
          --muted:#9AA4B2; --text:#E6F0FF; --accent:#4FC3F7; --primary:#2E5AAC;
        }
        body, .stApp { background: var(--bg); color: var(--text); }
        .pill{font-size:12px;padding:2px 8px;border-radius:999px;background:#0D1422;border:1px solid var(--border);}
        .muted{color:var(--muted)}
        .stContainer{background:var(--panel)}
        .stButton>button{
            background:#2E5AAC; color:#fff; border:1px solid rgba(255,255,255,.08);
            border-radius:12px; padding:.55rem .9rem;
        }
        .stButton>button:hover{ filter:brightness(1.1) }
        .stTextInput>div>div>input,.stTextArea textarea,.stSelectbox>div>div>div{ 
          background:#0D1422; color:#E6F0FF; border:1px solid var(--border); border-radius:10px;
        }
        .stRadio>div[role=radiogroup] label{ color:#DCEBFF }
        /* bordered containers */
        .st-emotion-cache-1r6slb0, .st-emotion-cache-1r6slb0:has(> .stContainer){ border:1px solid var(--border)!important; border-radius:16px!important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
