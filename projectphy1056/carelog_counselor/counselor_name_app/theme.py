# counselor_name_app/theme.py
from textwrap import dedent

def css_theme() -> str:
    return dedent("""
    <style>
      :root {
        --bg: #0f1720; --card:#111b27; --ink:#e7eef8; --muted:#a9b8ca;
        --accent:#6aa6ff; --accent-2:#5ee0a2; --warn:#ffd166; --danger:#ff6b6b;
        --ok:#22c55e; --border:#1e2a3a;
      }

      /* App base */
      [data-testid="stAppViewContainer"] {
        background: var(--bg);
        color: var(--ink);
      }
      section[data-testid="stSidebar"] {
        background:#0d141d;
      }

      /* Hide default Streamlit page navigator if config.toml wasn't picked up */
      [data-testid="stSidebar"] [data-testid="stSidebarNav"],
      [data-testid="stSidebar"] nav[aria-label="Page navigation"] {
        display: none !important;
      }

      /* Cards, separators */
      .k-card { background: var(--card); border:1px solid var(--border);
                border-radius:16px; padding:16px; }
      .k-sep { height:1px; background:var(--border); margin:16px 0; }
      .muted { color: var(--muted); }
      .linkish { color: var(--accent); text-decoration:none; }

      /* Buttons */
      button, .k-btn { border-radius: 10px !important; }

      /* Metrics: stronger contrast */
      [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 700; }
      [data-testid="stMetricLabel"] { color: #d2deee !important; }

      /* Pills */
      .pill { padding:2px 8px; border-radius:999px; border:1px solid var(--border); }
      .pill.ok{ background:#0f2a1b; border-color:#164430; }
      .pill.warn{ background:#2a240f; border-color:#4d3c11; }
      .pill.bad{ background:#2a1313; border-color:#4d1717; }
      .tag { font-size:12px; opacity:0.9; }
    </style>
    """)
