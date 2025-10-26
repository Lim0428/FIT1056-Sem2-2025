import streamlit as st
from typing import List, Dict

def notes_table(notes: List[Dict]):
    if not notes:
        st.write("No notes yet.")
        return
    for n in sorted(notes, key=lambda x: x.get("ts",""), reverse=True):
        with st.container():
            st.markdown(f"**{n['title']}**  ·  {n['ts']}  ·  template: `{n['template']}`")
            st.code(n.get("content"))
            st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)
