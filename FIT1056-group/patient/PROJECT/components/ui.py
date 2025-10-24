import streamlit as st
from contextlib import contextmanager

# Call this at the top of every page (and in carelog_main.py) once
def apply_theme():
    st.markdown(
        """
        <style>
        /* Layout tweaks */
        .block-container { padding-top: 2rem; max-width: 900px; }

        /* Design tokens (use Streamlit theme colors where possible) */
        :root{
          --primary: var(--primary-color, #3E7BFA);
          --bg: #0f1221;
          --bg-2: #171b2e;
          --text: #E6ECFF;
          --muted: #9BA9D7;
          --good: #27C193;
          --warn: #FFC857;
          --bad:  #FF6B6B;
          --card-radius: 16px;
          --shadow: 0 8px 30px rgba(0,0,0,.18);
        }

        /* Headings with accent bar */
        .cl-header{
          background: linear-gradient(135deg, rgba(62,123,250,.15), rgba(62,123,250,.05));
          border: 1px solid rgba(255,255,255,.06);
          border-left: 6px solid var(--primary);
          padding: 14px 16px;
          border-radius: 14px;
          margin: 8px 0 18px;
          box-shadow: 0 6px 18px rgba(0,0,0,.12);
        }
        .cl-header h1, .cl-header h2{
          margin: 0;
          font-weight: 700;
          letter-spacing: .3px;
        }
        .cl-sub{ color: var(--muted); margin-top: 6px; }

        /* Card block */
        .cl-card{
          background: var(--bg-2);
          border: 1px solid rgba(255,255,255,.06);
          border-radius: var(--card-radius);
          padding: 16px 18px;
          margin: 10px 0 18px;
          box-shadow: var(--shadow);
        }

        /* Badge pill */
        .cl-badge{
          display:inline-block;
          background: rgba(62,123,250,.18);
          border:1px solid rgba(62,123,250,.35);
          color:#cfe0ff;
          padding: 4px 10px;
          border-radius: 999px;
          font-size: 12px;
          letter-spacing: .2px;
        }

        /* Buttons */
        .stButton>button{
          background: var(--primary);
          color: white;
          border: none;
          border-radius: 12px;
          padding: 0.6rem 1rem;
          font-weight: 600;
          box-shadow: 0 8px 18px rgba(62,123,250,.35);
        }
        .stButton>button:hover{
          filter: brightness(1.05);
        }

        /* Inputs */
        .stTextInput>div>div>input,
        .stTextArea textarea,
        .stSelectbox>div>div>div,
        .stDateInput>div>div>input,
        .stTimeInput>div>div>input{
          background: rgba(255,255,255,.02);
          border-radius: 10px;
        }

        /* Divider */
        .cl-divider{ border-bottom:1px solid rgba(255,255,255,.08); margin: 16px 0; }

        </style>
        """,
        unsafe_allow_html=True,
    )

def divider():
    st.markdown("<div class='cl-divider'></div>", unsafe_allow_html=True)

def badge(text: str):
    st.markdown(f"<span class='cl-badge'>{text}</span>", unsafe_allow_html=True)

def page_header(title: str, subtitle: str = "", emoji: str = ""):
    icon = f"{emoji} " if emoji else ""
    html = f"<div class='cl-header'><h1>{icon}{title}</h1>"
    if subtitle:
        html += f"<div class='cl-sub'>{subtitle}</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

@contextmanager
def card(title: str = ""):
    st.markdown("<div class='cl-card'>", unsafe_allow_html=True)
    if title:
        st.markdown(f"**{title}**")
    yield
    st.markdown("</div>", unsafe_allow_html=True)

def require_auth():
    if "auth_user" not in st.session_state or not st.session_state.auth_user:
        st.info("Please log in on the Home page first.")
        st.stop()

def current_user_id():
    return st.session_state.get("auth_user")

def divider():
    st.markdown("---")

def badge(text: str):
    st.markdown(
        "<span style='background:#EEF3FF;padding:4px 8px;border-radius:8px'>"
        f"{text}</span>",
        unsafe_allow_html=True,
    )

def require_auth():
    if "auth_user" not in st.session_state or not st.session_state.auth_user:
        st.info("Please log in on the Home page first.")
        st.stop()

def current_user_id():
    return st.session_state.get("auth_user")
