# counselor_name_components/forms.py
import streamlit as st
import pandas as pd
from typing import Dict, List

# =========================
# Session Note Templates
# =========================
SOAP_FIELDS = [
    ("Subjective", "Patient-reported feelings, symptoms"),
    ("Objective",  "Observable facts, MSE, appearance"),
    ("Assessment", "Clinical formulation / diagnosis"),
    ("Plan",       "Interventions, homework, follow-up"),
]

DARE_FIELDS = [
    ("Data",       "Context, presenting problem, history"),
    ("Assessment", "Clinician assessment"),
    ("Response",   "Interventions and patient response"),
    ("Evaluation", "Outcomes, progress, plan"),
]

ENCOUNTER_MODES = ["In-person", "Video", "Phone"]
RISK_LEVELS = ["None", "Low", "Moderate", "High"]


def session_note_form(template: str = "SOAP", initial: Dict | None = None) -> Dict:
    """
    Returns a dict: {title, template, content, meta}
    """
    initial = initial or {}

    # Header fields
    cols = st.columns(3)
    title = cols[0].text_input(
        "Title",
        value=initial.get("title", f"{template} session"),
    )
    session_date = cols[1].date_input("Session date")
    duration_mins = cols[2].number_input(
        "Duration (mins)", min_value=0, max_value=240,
        value=int(initial.get("meta", {}).get("duration_mins", 50))
    )

    mode = st.selectbox(
        "Mode",
        ENCOUNTER_MODES,
        index=ENCOUNTER_MODES.index(
            initial.get("meta", {}).get("mode", "In-person")
        ) if initial.get("meta") else 0,
    )

    st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

    # Body sections
    fields = SOAP_FIELDS if template == "SOAP" else DARE_FIELDS
    content_defaults = initial.get("content", {})
    content: Dict[str, str] = {}
    for label, hint in fields:
        content[label] = st.text_area(
            label, value=content_defaults.get(label, ""),
            placeholder=hint, height=110
        )

    st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

    # Risk & meta
    c1, c2, c3 = st.columns(3)
    risk_level = c1.selectbox(
        "Risk level",
        RISK_LEVELS,
        index=RISK_LEVELS.index(
            initial.get("meta", {}).get("risk_level", "None")
        ) if initial.get("meta") else 0,
    )
    safeguarding = c2.checkbox(
        "Safeguarding action taken",
        value=bool(initial.get("meta", {}).get("safeguarding", False)),
    )
    consent_discussed = c3.checkbox(
        "Consent discussed/confirmed",
        value=bool(initial.get("meta", {}).get("consent_discussed", True)),
    )

    goals = st.text_input(
        "Goals (comma separated)",
        value=", ".join(initial.get("meta", {}).get("goals", [])),
    )
    tags = st.text_input(
        "Tags (comma separated)",
        value=", ".join(initial.get("meta", {}).get("tags", [])),
    )
    signature = st.text_input(
        "Clinician signature",
        value=initial.get("meta", {}).get("signature", ""),
    )

    meta = {
        "date": str(session_date),
        "duration_mins": int(duration_mins),
        "mode": mode,
        "risk_level": risk_level,
        "safeguarding": safeguarding,
        "consent_discussed": consent_discussed,
        "goals": [g.strip() for g in goals.split(",") if g.strip()],
        "tags":  [t.strip() for t in tags.split(",") if t.strip()],
        "signature": signature.strip(),
    }

    return {"title": title, "template": template, "content": content, "meta": meta}


# =========================
# Quick Assessments (Pro)
# =========================
PHQ9_LABELS = [f"PHQ-9 Q{i+1} (0–3)" for i in range(9)]
GAD7_LABELS = [f"GAD-7 Q{i+1} (0–3)" for i in range(7)]

def _severity_badge(label: str) -> str:
    cls = {
        "Minimal": "ok",
        "Mild": "ok",
        "Moderate": "warn",
        "Moderately Severe": "warn",
        "Severe": "bad",
    }.get(label, "ok")
    return f"<span class='pill {cls} tag'>{label}</span>"

def render_quick_assessments(patient_id: str, counselor_id: str):
    """
    Professional, compact panel with live scoring, severity badge,
    guidance text, and one-click save.
    """
    from counselor_name_app.services.assessments import AssessmentService
    svc = AssessmentService()

    st.subheader("Quick Assessments")

    # PHQ-9
    with st.expander("PHQ-9 (Depression)"):
        cols = st.columns(3)
        a = []
        for i, lbl in enumerate(PHQ9_LABELS):
            with cols[i % 3]:
                a.append(st.number_input(lbl, min_value=0, max_value=3, value=0, step=1, key=f"phq9_{i}"))
        res = svc.score_phq9(a)
        st.markdown(
            f"""
            <div class='k-card' style='margin-top:8px;'>
              <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div><b>Score:</b> {res['score']} {_severity_badge(res['band'])}</div>
                <div class='muted' style='font-size:12px;'>Tool: PHQ-9</div>
              </div>
              <div style='margin-top:6px;'>{res.get('guidance','')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        save_col, _ = st.columns([1,3])
        if save_col.button("Save PHQ-9", use_container_width=True, key="save_phq9_btn"):
            svc.save(patient_id, counselor_id, res)
            st.success("PHQ-9 saved to record.")

    # GAD-7
    with st.expander("GAD-7 (Anxiety)"):
        cols = st.columns(3)
        a = []
        for i, lbl in enumerate(GAD7_LABELS):
            with cols[i % 3]:
                a.append(st.number_input(lbl, min_value=0, max_value=3, value=0, step=1, key=f"gad7_{i}"))
        res = svc.score_gad7(a)
        st.markdown(
            f"""
            <div class='k-card' style='margin-top:8px;'>
              <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div><b>Score:</b> {res['score']} {_severity_badge(res['band'])}</div>
                <div class='muted' style='font-size:12px;'>Tool: GAD-7</div>
              </div>
              <div style='margin-top:6px;'>{res.get('guidance','')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        save_col, _ = st.columns([1,3])
        if save_col.button("Save GAD-7", use_container_width=True, key="save_gad7_btn"):
            svc.save(patient_id, counselor_id, res)
            st.success("GAD-7 saved to record.")


# =========================
# Safety Plan (Pro)
# =========================
def safety_plan_form_pro(initial: Dict | None = None) -> Dict:
    """
    Stanley-Brown style:
    1) Warning signs  2) Internal coping  3) Distractions (people/places)
    4) Support contacts  5) Professionals/agencies  6) Restrict means
    7) Reasons for living  8) Crisis steps  9) Environment safety  10) Sharing
    """
    initial = initial or {}
    st.info("Safety plans can be shared with the patient and on-call staff. Update and version as needed.")

    # 1–3: text lists
    c1, c2, c3 = st.columns(3)
    with c1:
        warning = st.text_area(
            "Warning signs",
            value="\n".join(initial.get("warning_signs", [])),
            placeholder="Thoughts, images, mood, situation, behavior… (one per line)",
            height=120,
        )
    with c2:
        coping = st.text_area(
            "Internal coping strategies",
            value="\n".join(initial.get("internal_coping", [])),
            placeholder="Breathing, grounding, music, journaling… (one per line)",
            height=120,
        )
    with c3:
        distractions = st.text_area(
            "People & places for distraction",
            value="\n".join(initial.get("distractions", [])),
            placeholder="Gym, park, café, friend’s house… (one per line)",
            height=120,
        )

    # 4) Contacts for help (friends/family)
    st.markdown("**Support contacts**")
    sup_df = (
        pd.DataFrame(initial.get("support_contacts", []))
        if initial.get("support_contacts")
        else pd.DataFrame(columns=["name", "relationship", "phone"])
    )
    sup = st.data_editor(
        sup_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={"name": "Name", "relationship": "Relationship", "phone": "Phone"},
    )

    # 5) Professionals / agencies
    st.markdown("**Professionals & agencies**")
    pro_df = (
        pd.DataFrame(initial.get("professional_contacts", []))
        if initial.get("professional_contacts")
        else pd.DataFrame(
            [
                {"service": "Counselor", "name": "", "phone": ""},
                {"service": "Clinic / GP", "name": "", "phone": ""},
                {"service": "Emergency", "name": "999 / 112", "phone": ""},
                {"service": "Crisis Line", "name": "Talian Kasih 15999", "phone": ""},
            ]
        )
    )
    pros = st.data_editor(
        pro_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={"service": "Service", "name": "Name", "phone": "Phone"},
    )

    # 6–9: text sections
    means = st.text_area(
        "Means restriction plan",
        value=initial.get("means_restriction", ""),
        placeholder="Remove or secure medications, sharps, ligatures, firearms, etc.",
    )
    reasons = st.text_area(
        "Reasons for living",
        value=initial.get("reasons_for_living", ""),
        placeholder="What keeps you going? People, goals, values…",
    )
    crisis_steps = st.text_area(
        "Crisis steps",
        value="\n".join(initial.get("crisis_steps", [])),
        placeholder="1) ..., 2) ..., 3) ... (one step per line)",
        height=110,
    )
    env = st.text_area(
        "Environment safety",
        value=initial.get("environment", ""),
        placeholder="Where to stay tonight? Who can you be with? How to stay safe at home?",
    )

    # 10) Sharing toggles
    s1, s2 = st.columns(2)
    share_patient = s1.toggle("Share with patient", value=bool(initial.get("shared", {}).get("patient", True)))
    share_team = s2.toggle("Share with care team", value=bool(initial.get("shared", {}).get("care_team", True)))

    return {
        "warning_signs": [x.strip() for x in warning.splitlines() if x.strip()],
        "internal_coping": [x.strip() for x in coping.splitlines() if x.strip()],
        "distractions": [x.strip() for x in distractions.splitlines() if x.strip()],
        "support_contacts": sup.to_dict(orient="records"),
        "professional_contacts": pros.to_dict(orient="records"),
        "means_restriction": means.strip(),
        "reasons_for_living": reasons.strip(),
        "crisis_steps": [x.strip() for x in crisis_steps.splitlines() if x.strip()],
        "environment": env.strip(),
        "shared": {"patient": bool(share_patient), "care_team": bool(share_team)},
    }
