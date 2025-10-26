# admin_name_components/widgets.py
import streamlit as st

def page_header(title: str, subtitle: str = ""):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)

def metric_row(metrics):
    cols = st.columns(len(metrics))
    for col, (label, value, help_txt) in zip(cols, metrics):
        with col:
            st.metric(label, value, help=help_txt)

def card():
    return st.container(border=True)
