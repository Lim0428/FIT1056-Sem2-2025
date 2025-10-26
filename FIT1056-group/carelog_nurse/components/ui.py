# carelog_nurse/components/ui.py
import streamlit as st

def apply_theme():
    st.markdown("""
    <style>
      /* ===== Kill the white Streamlit header/toolbar ===== */
      header[data-testid="stHeader"] { display: none; }        /* main white bar */
      div[data-testid="stToolbar"] { display: none !important; }/* deploy/menu toolbar */
      div[data-testid="stDecoration"] { display: none !important; } /* tiny accent strip on some builds */

      /* ===== App canvas & sidebar ===== */
      [data-testid="stAppViewContainer"]{ background:#0b1320; color:#e8eef6; }
      .block-container{ max-width:1400px; padding-top: 8px; padding-bottom:48px; } /* pull content up */
      main .block-container { padding-top: 8px; } /* extra safety for newer builds */

      section[data-testid="stSidebar"]{ background:#0f1726; color:#fff !important; }
      section[data-testid="stSidebar"] *{ color:#fff !important; }
      :root{ --card:#0f1a2b; --line:#1a2c45; --muted:#9fb0c3; }

      /* Header card */
      .hdr{ display:flex; align-items:center; gap:12px; background:var(--card);
            border:1px solid var(--line); border-radius:18px; padding:14px 16px; margin-bottom:12px; }
      .hdr .tit{ font-size:20px; font-weight:900; margin:0; }
      .muted{ color:var(--muted); }

      /* KPI grid (single block so it doesn’t stack) */
      .kpis{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
      .kpi{ border-radius:18px; padding:16px 18px; color:#0b1320; box-shadow:0 2px 14px rgba(0,0,0,.25); }
      .kpi h4{ margin:0 0 8px 0; font-size:13px; font-weight:700; color:#eef3ff; opacity:.9; }
      .kpi .big{ font-size:28px; font-weight:800; color:#fff; line-height:1.1; }
      .kpi .sub{ font-size:12px; color:#f5f7ff; opacity:.85; }
      .doctor{ background:linear-gradient(135deg,#5cc6ff 0%,#1d88ff 100%); }
      .patient{ background:linear-gradient(135deg,#5cf0c5 0%,#2fbf9f 100%); }
      .surgery{ background:linear-gradient(135deg,#e574ff 0%,#b24bff 100%); }
      .report{ background:linear-gradient(135deg,#ff8b8b 0%,#ff4141 100%); }

      /* Panels & lists */
      .panel{ background:var(--card); border:1px solid var(--line); border-radius:18px; padding:16px; }
      .panel h3{ margin:0 0 12px 0; font-size:16px; font-weight:800; color:#eaf2ff; }
      .mini-row{ display:flex; align-items:center; justify-content:space-between; padding:8px 0; border-bottom:1px solid var(--line); }
      .mini-left{ display:flex; align-items:center; gap:10px; }
      .avatar{ width:26px; height:26px; border-radius:999px; background:#22324a; display:inline-block; }
      .time{ font-size:12px; color:#b9c7da; }
      .vega-embed summary{ display:none; } /* remove Altair "View Source" disclosure triangle */
    </style>
    """, unsafe_allow_html=True)

def page_header(title: str, subtitle: str = "", emoji: str = "🏠"):
    st.markdown(
        f"""
        <div class="hdr">
          <div style="font-size:26px">{emoji}</div>
          <div>
            <div class="tit">{title}</div>
            <div class="muted">{subtitle}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def kpi_row_colored(items):
    tiles = []
    for it in items:
        tiles.append(
            f"""<div class="kpi {it.get('class','doctor')}">
                  <h4>{it.get('label','')}</h4>
                  <div class="big">{it.get('value','—')}</div>
                  <div class="sub">{it.get('hint','')}</div>
                </div>"""
        )
    st.markdown('<div class="kpis">' + "".join(tiles) + "</div>", unsafe_allow_html=True)

def page_header(title: str, subtitle: str = "", emoji: str = "🏠"):
    st.markdown(
        f"""
        <div class="hdr">
          <div style="font-size:26px">{emoji}</div>
          <div>
            <div class="tit">{title}</div>
            <div class="muted">{subtitle}</div>
          </div>
        </div>
        """, unsafe_allow_html=True
    )

def kpi_row_colored(items):
    # Build one HTML string so tiles are truly in the same grid
    tiles = []
    for it in items:
        tiles.append(
            f"""<div class="kpi {it.get('class','doctor')}">
                  <h4>{it.get('label','')}</h4>
                  <div class="big">{it.get('value','—')}</div>
                  <div class="sub">{it.get('hint','')}</div>
                </div>"""
        )
    html = '<div class="kpis">' + "".join(tiles) + "</div>"
    st.markdown(html, unsafe_allow_html=True)
