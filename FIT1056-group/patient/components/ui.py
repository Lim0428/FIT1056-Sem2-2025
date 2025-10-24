# components/ui.py — Final Dark Mode with Always-Visible Sidebar
import contextlib
import streamlit as st

# -----------------------------------------------------------------------------
# Dark theme & UI system
# -----------------------------------------------------------------------------
def apply_theme(
    *,
    primary: str = "#7CB4FF",   # Accent blue
    bg: str = "#0A0D14",        # App background
    surface: str = "#111827",   # Card surfaces
    text: str = "#F5F7FA",      # Bright readable text
    muted: str = "#C5CEE0",     # Secondary text (labels)
) -> None:
    """Enhanced dark theme with always-visible sidebar and good contrast."""
    st.markdown(
        f"""
        <style>
        :root {{
          --primary: {primary};
          --bg: {bg};
          --surface: {surface};
          --text: {text};
          --muted: {muted};
          --border: rgba(255,255,255,0.08);
        }}

        /* --- GLOBAL BACKGROUND --- */
        html, body {{
          background-color: var(--bg) !important;
          color: var(--text) !important;
        }}
        [data-testid="stAppViewContainer"] {{
          background-color: var(--bg) !important;
          z-index: 0 !important;
        }}

        /* --- SIDEBAR: always visible, fixed position --- */
        section[data-testid="stSidebar"] {{
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
          transform: translateX(0%) !important;
          background-color: #0D111C !important;
          border-right: 1px solid var(--border);
          box-shadow: 2px 0 20px rgba(0,0,0,0.45);
          color: var(--text) !important;
          z-index: 20 !important;
          position: relative !important;
        }}
        section[data-testid="stSidebar"] * {{
          color: var(--text) !important;
        }}
        section[data-testid="stSidebar"] div[role="tablist"] button {{
          background: transparent !important;
          color: var(--muted) !important;
          border-radius: 8px;
          margin: 2px 4px;
          transition: all 0.2s ease;
        }}
        section[data-testid="stSidebar"] div[role="tablist"] button:hover {{
          background-color: rgba(124,180,255,0.15) !important;
          color: var(--text) !important;
        }}
        section[data-testid="stSidebar"] div[role="tablist"] button[aria-selected="true"] {{
          background: linear-gradient(90deg, rgba(124,180,255,0.3), rgba(124,180,255,0.1));
          color: var(--text) !important;
          font-weight: 600 !important;
          box-shadow: inset 0 0 6px rgba(124,180,255,0.3);
        }}

        /* --- HEADER CARD --- */
        .cl-header {{
          background: linear-gradient(145deg, rgba(124,180,255,0.18), rgba(255,255,255,0.04));
          border-radius: 16px;
          border: 1px solid var(--border);
          padding: 18px 20px;
          margin: 10px 0 20px;
        }}
        .cl-header h1 {{ color: var(--text); font-weight: 900; margin: 0; }}
        .cl-sub {{ color: var(--muted); font-size: 15px; }}

        /* --- CARDS --- */
        .cl-card {{
          background-color: var(--surface);
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 20px;
          margin-bottom: 20px;
          box-shadow: 0 6px 25px rgba(0,0,0,0.35);
        }}
        .cl-card h3, .cl-card h4, .cl-card strong {{ color: var(--text); }}
        .cl-card p, .cl-card small, .cl-card span {{ color: var(--muted); }}

        /* --- TEXT CONTRAST --- */
        .stMarkdown, .stText, .stCaption, .stTextInput, label {{
          color: var(--text) !important;
        }}

        /* --- INPUT FIELDS --- */
        input, textarea, select {{
          background-color: #131B2C !important;
          color: var(--text) !important;
          border: 1.25px solid #2C395A !important;
          border-radius: 10px !important;
        }}
        input:focus, textarea:focus, select:focus {{
          outline: none !important;
          border-color: var(--primary) !important;
          box-shadow: 0 0 6px rgba(124,180,255,0.4);
        }}

        /* --- BUTTONS --- */
        .stButton > button {{
          background: var(--primary) !important;
          color: #0B0F19 !important;
          border-radius: 10px !important;
          font-weight: 700 !important;
          box-shadow: 0 4px 15px rgba(124,180,255,.3);
          border: none !important;
          transition: all 0.2s ease-in-out;
        }}
        .stButton > button:hover {{
          transform: translateY(-2px);
          box-shadow: 0 6px 18px rgba(124,180,255,.45);
        }}

        /* --- ALERT BOXES --- */
        .stAlert {{
          background: rgba(255,255,255,0.08) !important;
          border: 1px solid rgba(255,255,255,0.12) !important;
          color: var(--text) !important;
        }}

        /* --- METRICS / LABELS --- */
        .stMetric-label {{ color: var(--muted) !important; }}
        .stMetric-value {{ color: var(--text) !important; font-weight: 800; }}

        /* --- TABLES --- */
        .stDataFrame, .stTable {{
          background-color: var(--surface) !important;
          border-radius: 12px !important;
          border: 1px solid rgba(255,255,255,0.08);
        }}
        .stTable th, .stTable td {{
          color: var(--text) !important;
          border-color: rgba(255,255,255,0.1) !important;
        }}

        /* --- REMOVE STREAMLIT DEFAULT FOOTER --- */
        #MainMenu, header, footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Header and card components
# -----------------------------------------------------------------------------
def page_header(title: str, subtitle: str = "", emoji: str = "✨") -> None:
    """Nice header block used on each page."""
    st.markdown(
        f"""
        <div class="cl-header">
            <div class="cl-header-emoji">{emoji}</div>
            <div>
                <h1>{title}</h1>
                {'<div class="cl-sub">'+subtitle+'</div>' if subtitle else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@contextlib.contextmanager
def card(title: str | None = None):
    """Container with matching dark card styling."""
    st.markdown('<div class="cl-card">', unsafe_allow_html=True)
    if title:
        st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
    try:
        yield
    finally:
        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Optional lightweight auth gate used by your pages
# -----------------------------------------------------------------------------
def require_auth() -> None:
    """Guard pages that need login; expects st.session_state['auth_user'] to exist when logged in."""
    if "auth_user" not in st.session_state or not st.session_state["auth_user"]:
        with card():
            st.warning("Please log in on the **Home** page first to continue.")
        st.stop()


# -----------------------------------------------------------------------------
# Divider helper
# -----------------------------------------------------------------------------
def divider():
    st.markdown('<div class="cl-divider"></div>', unsafe_allow_html=True)
