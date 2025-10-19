# gui/components.py
import streamlit as st

def page_header(title: str, subtitle: str = "", icon: str = "🎵"):
    with st.container():
        st.markdown(
            f"""
            <div class="app-title">
                <h1>{icon} {title}</h1>
                {f"<small>{subtitle}</small>" if subtitle else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")  # spacing after hero

def stat_cards(items):
    cols = st.columns(len(items))
    for col, it in zip(cols, items):
        with col:
            with st.container():
                st.markdown('<div class="ui-card">', unsafe_allow_html=True)
                st.markdown(f"<h3>{it.get('icon','')} {it['label']}</h3>", unsafe_allow_html=True)
                st.markdown(f"<div class='ui-kpi'>{it['value']}</div>", unsafe_allow_html=True)
                if it.get("help"):
                    st.markdown(f"<div class='ui-kpi-label'>{it['help']}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

def sidebar_persona(user, manager):
    """
    Clean persona shown in the sidebar.
    """
    name = user.get("username", "")
    role = user.get("role")
    uid  = user.get("user_id")

    avatar_url = (
        "https://ui-avatars.com/api/"
        f"?name={name.replace(' ', '+')}&background=4C6EF5&color=fff&rounded=true&bold=true"
    )

    lines = []
    if role == "student":
        stu = manager.find_student_by_id(int(uid)) if str(uid).isdigit() else None
        if stu:
            lines.append(f"Instrument: **{getattr(stu, 'instrument', 'N/A')}**")
            lines.append(f"Enrolled: **{len(getattr(stu,'enrolled_course_ids',[]) or [])}**")
            lines.append(f"Balance: **{getattr(stu,'balance',0.0):.2f}**")
    elif role == "teacher":
        t = manager.find_teacher_by_id(int(uid)) if str(uid).isdigit() else None
        if t:
            lines.append(f"Speciality: **{getattr(t,'speciality','Unknown')}**")
    else:
        lines.append("Staff account")

    st.markdown('<div class="persona-card">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown('<div class="persona-avatar">', unsafe_allow_html=True)
        st.image(avatar_url, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f"<p class='persona-name'>{name}</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='persona-meta'>ID: <code>{uid}</code> · Role: <strong>{role}</strong></div>", unsafe_allow_html=True)
        if lines:
            st.write("")
            for ln in lines:
                st.markdown(f"- {ln}")
    st.markdown('</div>', unsafe_allow_html=True)
