import streamlit as st
from components.ui import apply_theme, page_header, card, require_auth
from app.patient import PatientService

st.set_page_config(page_title="Feedback", page_icon="🗳️", layout="wide")
apply_theme()
require_auth()
page_header("Feedback", "Tell us how we are doing", "🗳️")

svc = PatientService()
pid = st.session_state["auth_user"]

def star_slider(label: str, key: str = "stars", default: int = 5) -> int:
    """
    A 1–5 slider with a big star preview (★★★★★).
    Returns the selected integer.
    """
    # subtle CSS to make the preview large and pretty
    st.markdown("""
    <style>
      .star-preview {
        font-size: 28px; 
        line-height: 1.1;
        letter-spacing: 2px;
        margin: .25rem 0 .75rem 0;
      }
      .star-preview .on  { color: #F59E0B; }     /* amber-500 */
      .star-preview .off { color: #E5E7EB; }     /* gray-200  */
    </style>
    """, unsafe_allow_html=True)

    val = st.slider(label, 1, 5, value=default, step=1, key=key)
    on  = "★" * val
    off = "☆" * (5 - val)
    st.markdown(f"<div class='star-preview'><span class='on'>{on}</span><span class='off'>{off}</span></div>", unsafe_allow_html=True)
    return val

with card("Submit feedback"):
    rating = star_slider("Rating", key="fb_rating", default=5)  # <-- ⭐ slider
    text = st.text_area("Comments")
    if st.button("Submit"):
        svc.add_feedback(pid, {"rating": int(rating), "text": text})
        st.success("Thank you! Your feedback has been submitted.")

with card("Your feedback history"):
    items = list(reversed(svc.get_feedback(pid)))
    if not items:
        st.info("No feedback yet.")
    else:
        for f in items:
            on  = "★" * int(f.get("rating", 0))
            off = "☆" * (5 - int(f.get("rating", 0)))
            st.write(f"• **{f['ts']}** — {on}{off}")
            if f.get("text"):
                st.caption(f["text"])