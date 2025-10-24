import streamlit as st
from typing import Optional
from urllib.parse import quote
from streamlit.components.v1 import html as st_html

# =========================
# Desktop theme & styles for the main app (unchanged)
# =========================
def apply_desktop_css(max_w: int = 1400):
    st.markdown(
        f"""
        <style>
        .block-container {{ max-width:{max_w}px; }}

        .cl-card {{
            background:#0f172a; border:1px solid #1f2937;
            border-radius:16px; padding:16px;
        }}

        .cl-stat {{
            background:#101826; border:1px solid #1e293b;
            border-radius:14px; padding:14px 16px;
        }}
        .cl-stat .lbl {{ opacity:.8; font-size:12px; }}
        .cl-stat .val {{ font-size:24px; font-weight:700; }}

        .chip {{ display:inline-block; padding:2px 10px; border-radius:999px;
                 background:rgba(82,133,247,.18); color:#cfe0ff; font-size:12px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================
# Header / sections
# =========================
def page_header(title: str, subtitle: Optional[str] = None, right: Optional[str] = None):
    left, right_col = st.columns([1, 0.15])
    with left:
        st.markdown(f"## {title}")
        if subtitle:
            st.caption(subtitle)
    if right:
        with right_col:
            st.markdown(f"<span class='chip'>{right}</span>", unsafe_allow_html=True)

def stat(label: str, value: str, sub: Optional[str] = None):
    st.markdown(
        f"""
        <div class="cl-stat">
            <div class="lbl">{label}</div>
            <div class="val">{value}</div>
            {"<div class='lbl' style='margin-top:4px'>"+sub+"</div>" if sub else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def card(title: str, body_md: str, footer_md: Optional[str] = None):
    st.markdown(
        f"<div class='cl-card'><h4 style='margin:0 0 6px 0'>{title}</h4>{body_md}"
        f"{('<div style=\"opacity:.7;margin-top:8px\">'+footer_md+'</div>') if footer_md else ''}</div>",
        unsafe_allow_html=True,
    )

# =========================
# Quick Action card — card itself is clickable, same tab, no extra boxes
# Implemented as a Streamlit component so JS navigation is reliable
# =========================
def action_card(title: str, subtitle: str, icon: str, *, target_page: str, key: str):
    """
    Renders a large visual card (same dimensions as before) and makes the entire
    card clickable. Clicking navigates in the SAME TAB to the Streamlit subpage.
    No additional buttons/boxes are rendered.
    """
    target_q = quote(target_page, safe="")
    st_html(
        f"""
        <style>
        /* Scoped to this component only */
        .qa-wrap-{key} {{
            position: relative;
            width: 100%;
        }}
        .qa-card-{key} {{
            background:#0f172a; border:1px solid #1f2937;
            border-radius:22px; padding:18px;
            display:flex; gap:14px; align-items:center;
            min-height:120px;                  /* keep exact height */
            box-shadow: 0 10px 24px rgba(0,0,0,.28);
            transition: border-color .12s ease, box-shadow .12s ease, transform .06s ease;
            user-select: none;
            cursor: pointer;
        }}
        .qa-card-{key}:hover {{
            border-color:#334155; box-shadow: 0 12px 28px rgba(0,0,0,.32);
            transform: translateY(-1px);
        }}
        .qa-icon-{key} {{ font-size:40px; line-height:1; margin-right:2px; }}
        .qa-title-{key} {{ font-weight:800; font-size:18px; margin:0; color:#e5e7eb; }}
        .qa-sub-{key}   {{ opacity:.80; font-size:12.5px; margin-top:4px; color:#cbd5e1; }}
        </style>

        <div class="qa-wrap-{key}">
          <div class="qa-card-{key}" role="button" tabindex="0"
               onclick="(function(){{
                   const href='/?page={target_q}';
                   if (window.top) window.top.location.href = href;
                   else window.location.href = href;
               }})()"
               onkeydown="if(event.key==='Enter'||event.key===' ') {{
                   const href='/?page={target_q}';
                   if (window.top) window.top.location.href = href;
                   else window.location.href = href;
               }}">
            <div class="qa-icon-{key}">{icon}</div>
            <div>
              <div class="qa-title-{key}">{title}</div>
              <div class="qa-sub-{key}">{subtitle}</div>
            </div>
          </div>
        </div>
        """,
        height=140,           # matches min-height + padding; keeps your size
        scrolling=False,
    )
