# components/ui.py — Dark Mode + Always-Visible Sidebar + UI polish
import contextlib
import streamlit as st
import altair as alt

def apply_theme(
    *,
    primary: str = "#7CB4FF",
    bg: str = "#0B1220",          # page background
    surface: str = "#121A2C",     # card surface (a touch lighter than bg)
    text: str = "#F9FBFF",        # main text (very bright)
    muted: str = "#D7E1F9",       # secondary text (still bright & readable)
) -> None:
    """Dark theme with high-contrast text and controls."""
    st.markdown(
        f"""
        <style>
        :root {{
          --primary: {primary};
          --bg: {bg};
          --surface: {surface};
          --text: {text};
          --muted: {muted};
          --border: rgba(255,255,255,0.18);
        }}

        html, body, .stApp, [data-testid="stAppViewContainer"], .main, .block-container {{
          background-color: var(--bg) !important;
          color: var(--text) !important;
        }}

        /* remove header/decor gap */
        [data-testid="stHeader"], [data-testid="stDecoration"] {{
          height: 0 !important; visibility: hidden !important;
        }}
        .main .block-container {{ padding-top: 1rem !important; }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
          background-color: #0E1423 !important;
          border-right: 1px solid var(--border);
          box-shadow: 2px 0 20px rgba(0,0,0,.45);
        }}
        section[data-testid="stSidebar"] * {{ color: var(--text) !important; }}

        /* Header card */
        .cl-header {{
          background: linear-gradient(145deg, rgba(124,180,255,0.22), rgba(255,255,255,0.06));
          border: 1px solid var(--border);
          border-radius: 16px;
          padding: 18px 20px;
          margin: 10px 0 20px;
        }}
        .cl-header h1 {{
          color: var(--text);
          font-weight: 900;
          margin: 0;
          letter-spacing: .2px;
        }}
        .cl-sub {{ color: var(--muted); font-size: 15px; opacity: .95; }}

        /* Cards */
        .cl-card {{
          background-color: var(--surface);
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 20px;
          margin-bottom: 20px;
          box-shadow: 0 8px 28px rgba(0,0,0,.45);
        }}
        .cl-card h3, .cl-card h4, .cl-card strong {{ color: var(--text); }}
        .cl-card p, .cl-card small, .cl-card span {{ color: var(--muted); }}

        /* General text & captions */
        .stMarkdown, .stText, label, p, span, small {{
          color: var(--text) !important;
        }}
        .stCaption, .st-emotion-cache-16idsys p, .st-emotion-cache-1r6slb0 {{
          color: var(--muted) !important;
          opacity: .96 !important;
        }}

        /* Inputs */
        input, textarea, select {{
          background-color: #16223B !important;
          color: var(--text) !important;
          border: 1.25px solid #355180 !important;
          border-radius: 10px !important;
        }}
        input::placeholder, textarea::placeholder {{ color: #BFD1FA !important; opacity: .9; }}
        input:focus, textarea:focus, select:focus {{
          outline: none !important;
          border-color: var(--primary) !important;
          box-shadow: 0 0 8px rgba(124,180,255,.55);
        }}

        /* Buttons */
        .stButton > button {{
          background: var(--primary) !important;
          color: #08101E !important;
          border-radius: 10px !important;
          font-weight: 800 !important;
          box-shadow: 0 6px 20px rgba(124,180,255,.45);
          border: none !important;
        }}
        .stButton > button:hover {{
          transform: translateY(-1px);
          box-shadow: 0 8px 22px rgba(124,180,255,.6);
        }}

        /* Metrics */
        .stMetric-label {{ color: var(--muted) !important; opacity: 1 !important; font-weight: 700; }}
        .stMetric-value {{ color: var(--text) !important; font-weight: 900; }}

        /* Tables */
        .stDataFrame, .stTable {{
          background-color: var(--surface) !important;
          border-radius: 12px !important;
          border: 1px solid var(--border);
        }}
        .stTable th, .stTable td {{
          color: var(--text) !important;
          border-color: rgba(255,255,255,0.14) !important;
        }}

        /* Alerts */
        .stAlert {{
          background: rgba(255,255,255,0.10) !important;
          border: 1px solid rgba(255,255,255,0.22) !important;
          color: var(--text) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def set_altair_dark_theme():
    """High-contrast Altair theme so chart labels are readable on dark bg."""
    def _theme():
        return {
            "config": {
                "background": "#0B1220",
                "view": {"stroke": "transparent"},
                "font": "Inter, Segoe UI, Roboto, sans-serif",
                "axis": {
                    "titleColor": "#F9FBFF",
                    "labelColor": "#F2F6FF",
                    "gridColor": "#2B3B5F",
                    "domainColor": "#2B3B5F",
                    "labelFontSize": 12,
                    "titleFontSize": 13,
                },
                "legend": {
                    "labelColor": "#F2F6FF",
                    "titleColor": "#FFFFFF",
                },
                "title": {"color": "#FFFFFF"},
                "range": {
                    "category": [
                        "#7CB4FF","#FF9F7C","#A7F06E","#FDD663",
                        "#B388FF","#68EDC6","#FFA9D1"
                    ]
                }
            }
        }
    alt.themes.register("cl_dark", _theme)
    alt.themes.enable("cl_dark")


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


def require_auth() -> None:
    """Guard pages that need login; expects st.session_state['auth_user'] to exist when logged in."""
    if "auth_user" not in st.session_state or not st.session_state["auth_user"]:
        with card():
            st.warning("Please log in on the **Home** page first to continue.")
        st.stop()


def divider():
    st.markdown('<div class="cl-divider" style="border-bottom:1px solid var(--border); margin: 16px 0;"></div>', unsafe_allow_html=True)
