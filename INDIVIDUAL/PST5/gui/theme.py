# gui/theme.py
import streamlit as st

def apply_theme():
    """
    Colorful gradient theme + crystal-clear tables and inputs,
    with EXTRA-STRONG contrast for sidebar labels (Change password).
    """

    # --- Theme selector
    with st.sidebar:
        st.markdown("#### 🎨 Theme")
        accent = st.selectbox(
            "Accent",
            ["violet", "blue", "teal", "green", "amber", "pink", "sunset"],
            key="__accent__",
        )

    accents = {
        "violet": {"a1": "#6E56CF", "a2": "#8E6BF0"},
        "blue":   {"a1": "#2563EB", "a2": "#38BDF8"},
        "teal":   {"a1": "#0D9488", "a2": "#22D3EE"},
        "green":  {"a1": "#16A34A", "a2": "#86EFAC"},
        "amber":  {"a1": "#F59E0B", "a2": "#FDE68A"},
        "pink":   {"a1": "#EC4899", "a2": "#F472B6"},
        "sunset": {"a1": "#F97316", "a2": "#EF4444"},
    }
    a = accents.get(st.session_state.get("__accent__", accent), accents["violet"])

    st.markdown(
        f"""
        <style>
        :root {{
          --bg: #0b1020;
          --bg-2: #0e1429;
          --card: rgba(255,255,255,0.06);
          --text: #E6EAF2;
          --muted: #A6B0CF;
          --primary: {a["a1"]};
          --primary-2: {a["a2"]};

          --table-border: #e5e7eb;
          --table-text: #111827;
          --table-zebra: #f8fafc;
          --table-header: #111827;
        }}

        /* Background */
        .stApp {{
          background:
            radial-gradient(1200px 800px at 10% -10%, #1d2443 0%, transparent 60%),
            radial-gradient(1200px 800px at 110% 10%, #24193d 0%, transparent 60%),
            linear-gradient(135deg, var(--bg), var(--bg-2));
          color: var(--text);
        }}
        .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}

        /* Hero */
        .app-title {{
          border-radius: 24px;
          padding: 24px 28px;
          background: linear-gradient(135deg,
            color-mix(in srgb, var(--primary) 25%, #000 75%) 0%,
            rgba(255,255,255,0.04) 100%);
          border: 1px solid rgba(255,255,255,0.08);
          box-shadow: 0 12px 30px rgba(0,0,0,0.35);
          position: relative; overflow: hidden;
        }}
        .app-title::after {{
          content: "";
          position: absolute; inset: -40%;
          background: radial-gradient(closest-side,
            color-mix(in srgb, var(--primary-2) 40%, transparent), transparent 70%);
          filter: blur(60px);
          animation: float 18s ease-in-out infinite alternate;
          opacity: 0.5;
        }}
        @keyframes float {{
          0% {{ transform: translate3d(10%, 0, 0); }}
          100% {{ transform: translate3d(-10%, -5%, 0); }}
        }}
        .app-title h1 {{
          margin: 0 0 6px 0;
          font-weight: 800;
          background: linear-gradient(90deg, var(--primary), var(--primary-2));
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
          font-size: 2.2rem;
        }}
        .app-title small {{ color: var(--muted); font-size: 0.95rem; }}

        /* Cards */
        .ui-card {{
          background: var(--card);
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 18px;
          padding: 16px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }}
        .ui-kpi {{
          font-size: 1.8rem;
          font-weight: 800;
          background: linear-gradient(90deg, var(--primary-2), var(--primary));
          -webkit-background-clip: text;
          color: transparent;
        }}

        /* ===== Buttons (Sign in = black text, including disabled) ===== */
        button[kind="primary"], .stButton>button {{
          background: linear-gradient(90deg, var(--primary-2), var(--primary)) !important;
          border: 0 !important;
          color: #000000 !important;
          font-weight: 700 !important;
          border-radius: 12px !important;
          box-shadow: 0 10px 24px rgba(0,0,0,.25) !important;
        }}
        .stButton>button:hover,
        .stButton>button:focus {{
          filter: brightness(1.05);
          transform: translateY(-1px);
          box-shadow: 0 16px 34px rgba(0,0,0,.35);
          color: #000000 !important;
        }}
        button[kind="primary"][disabled],
        .stButton>button[disabled],
        .stButton>button:disabled {{
          background: #ffffff !important;
          color: #000000 !important;
          border: 1px solid rgba(0,0,0,0.20) !important;
          opacity: 1 !important;
          box-shadow: none !important;
          filter: none !important;
          transform: none !important;
        }}

        /* ===== Inputs (white field + black text) ===== */
        .stTextInput input,
        .stNumberInput input,
        .stPassword input,
        textarea {{
          background: #ffffff !important;
          color: #111111 !important;
          caret-color: #111111 !important;
          font-weight: 600 !important;
          border-radius: 10px !important;
          border: 1px solid rgba(0,0,0,0.20) !important;
        }}
        .stTextInput input::placeholder,
        .stPassword input::placeholder,
        textarea::placeholder {{
          color: #6b7280 !important;
        }}
        .stTextInput > label,
        .stNumberInput > label,
        .stPassword > label,
        .stSelectbox > label {{
          color: var(--text) !important;
          font-weight: 600 !important;
        }}
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stPassword input:focus,
        textarea:focus {{
          outline: 2px solid color-mix(in srgb, var(--primary) 65%, #ffffff 0%) !important;
          box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 30%, transparent) !important;
          background: #ffffff !important;
          color: #111111 !important;
        }}
        .stTextInput input:disabled,
        .stPassword input:disabled {{
          background: #f3f4f6 !important;
          color: #9ca3af !important;
        }}

        /* ===== CRYSTAL-CLEAR TABLES ===== */
        .stTable, .stDataFrame {{
          background: #ffffff !important;
          color: var(--table-text) !important;
          border-radius: 14px !important;
          border: 1px solid var(--table-border) !important;
          box-shadow: 0 10px 24px rgba(0,0,0,0.22) !important;
        }}
        .stTable table {{ width: 100%; background: #ffffff !important; color: var(--table-text) !important; }}
        .stTable thead th {{
          position: sticky; top: 0;
          background: #ffffff !important;
          color: var(--table-header) !important;
          font-weight: 700 !important;
          border-bottom: 2px solid var(--table-border) !important;
          padding: 12px 14px !important;
        }}
        .stTable tbody td {{
          border-top: 1px solid var(--table-border) !important;
          padding: 10px 14px !important;
          color: var(--table-text) !important;
        }}
        .stTable tbody tr:nth-child(even) td {{ background: var(--table-zebra) !important; }}

        .stDataFrame [role="table"], .stDataFrame [data-testid="stDataFrame"] {{
          background: #ffffff !important; color: var(--table-text) !important;
        }}
        .stDataFrame [role="columnheader"] {{
          background: #ffffff !important; color: var(--table-header) !important;
          font-weight: 700 !important; border-bottom: 2px solid var(--table-border) !important;
        }}
        .stDataFrame [role="gridcell"] {{
          color: var(--table-text) !important; border-bottom: 1px solid var(--table-border) !important;
        }}
        .stDataFrame [role="row"]:nth-child(even) [role="gridcell"] {{ background: var(--table-zebra) !important; }}
        .stDataFrame ::-webkit-scrollbar {{ height: 12px; width: 12px; }}
        .stDataFrame ::-webkit-scrollbar-thumb {{ background: #d1d5db; border-radius: 10px; border: 3px solid #ffffff; }}
        .stDataFrame ::-webkit-scrollbar-track {{ background: #ffffff; }}

        /* ===== SUPER-STRONG SIDEBAR LABEL CONTRAST ===== */
        /* Force ALL labels in the sidebar (including inside Expanders) to be very dark & fully opaque */
        [data-testid="stSidebar"] label {{
          color: #0f172a !important;        /* slate-900 */
          font-weight: 800 !important;      /* extra bold */
          opacity: 1 !important;            /* override Streamlit's reduced opacity */
          text-shadow: none !important;
        }}
        /* Inputs in sidebar keep white background and dark text (already set globally) */
        [data-testid="stSidebar"] input::placeholder {{
          color: #334155 !important;        /* slate-700 placeholder for visibility */
        }}
        /* Sidebar expander title and helper text darker */
        [data-testid="stSidebar"] .st-expanderHeader p {{ color: #0f172a !important; font-weight: 800 !important; }}
        [data-testid="stSidebar"] .stMarkdown, 
        [data-testid="stSidebar"] .stCaption {{
          color: #334155 !important;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
        .stTabs [data-baseweb="tab"] {{
          background: var(--card);
          border-radius: 12px;
          border: 1px solid rgba(255,255,255,0.08);
        }}
        .stTabs [aria-selected="true"] {{ outline: 2px solid color-mix(in srgb, var(--primary) 50%, transparent); }}
        </style>
        """,
        unsafe_allow_html=True,
    )
