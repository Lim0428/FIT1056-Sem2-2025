import streamlit as st
import pandas as pd
from doctor_name_components.widgets import timestamp_label

def _auto_height(n_rows: int, row_height: int = 34, base: int = 56, max_h: int = 360) -> int:
    """Compute a tidy dataframe height."""
    return max(120, min(max_h, base + row_height * max(1, n_rows)))

def table_appointments(rows):
    if not rows:
        st.markdown(
            "<div class='metric-card' style='padding:12px;'>"
            "📅 <span class='muted'>No upcoming appointments.</span>"
            "</div>", unsafe_allow_html=True
        )
        return
    df = pd.DataFrame(rows)
    if "start" in df.columns:
        df["start"] = df["start"].apply(timestamp_label)
    if "end" in df.columns:
        df["end"] = df["end"].apply(timestamp_label)
    st.dataframe(df, use_container_width=True, hide_index=True, height=_auto_height(len(df)))

def table_patients(rows):
    if not rows:
        st.markdown(
            "<div class='metric-card' style='padding:12px;'>"
            "👥 <span class='muted'>No patients to display.</span>"
            "</div>", unsafe_allow_html=True
        )
        return
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True, height=_auto_height(len(df)))

def table_messages(rows):
    if not rows:
        st.markdown(
            "<div class='metric-card' style='padding:12px;'>"
            "💬 <span class='muted'>No messages.</span>"
            "</div>", unsafe_allow_html=True
        )
        return
    df = pd.DataFrame(rows)
    if "updated_at" in df.columns:
        df["updated_at"] = df["updated_at"].apply(timestamp_label)
    st.dataframe(df, use_container_width=True, hide_index=True, height=_auto_height(len(df)))
