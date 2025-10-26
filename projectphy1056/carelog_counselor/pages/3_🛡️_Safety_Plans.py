# pages/3_🛡️_Safety_Plans.py
import json
import streamlit as st
from io import StringIO
from datetime import datetime

from counselor_name_components.ui import apply_theme, top_nav, require_auth
from counselor_name_components.forms import safety_plan_form_pro
from counselor_name_app.services.patients import PatientService
from counselor_name_app.services.consent import ConsentService
from counselor_name_app.services.safety_plans import SafetyPlanService

st.set_page_config(page_title="Safety Plans", page_icon="🛡️", layout="wide")
apply_theme(); require_auth(); top_nav("Safety Plans")

me = st.session_state["auth_user"]
ps = PatientService()
consent = ConsentService()
sps = SafetyPlanService()

# ---------- Patient selection ----------
patients = ps.list_assigned(me)
if not patients:
    st.info("No assigned patients."); st.stop()

pid = st.selectbox("Patient", [p["id"] for p in patients],
                   format_func=lambda x: next(p['name'] for p in patients if p['id']==x))

if not consent.allowed(me, pid):
    with st.warning("Consent required. Use break-glass (audited) if clinically necessary."):
        reason = st.text_input("Reason for break-glass access")
        if st.button("Break-glass"):
            if reason.strip():
                consent.break_glass(me, pid, reason); st.success("Temporary access granted."); st.rerun()
            else:
                st.error("Reason is required.")
    st.stop()

st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)

# ---------- Layout: left form / right panel ----------
left, right = st.columns([1.8, 1])

with right:
    st.subheader("History & Actions")
    versions = sps.list_versions(pid)
    latest = versions[0] if versions else None

    if not versions:
        st.info("No safety plan on file yet. Create the first plan on the left.")
        selected_id = None
    else:
        labels = [f"v{p['version']} · {p['created_ts']} · {p['id']}" for p in versions]
        pick = st.selectbox("Versions (latest first)", options=labels)
        selected = versions[labels.index(pick)]
        selected_id = selected["id"]
        st.caption(f"Sharing: patient = {selected['shared'].get('patient', True)}, care team = {selected['shared'].get('care_team', True)}")
        st.caption(f"Updated: {selected.get('updated_ts', selected['created_ts'])}")

        # Download (JSON)
        plan_json = json.dumps(selected["content"], indent=2, ensure_ascii=False).encode("utf-8")
        st.download_button("Download JSON", data=plan_json, file_name=f"{pid}_safety_plan_{selected['id']}.json",
                           mime="application/json", use_container_width=True)

        # Markdown export (printable)
        def to_md(p: dict) -> str:
            c = p["content"]
            def lines(title, arr_or_text):
                if isinstance(arr_or_text, list):
                    s = "\n".join([f"- {x}" for x in arr_or_text]) or "_(none)_"
                else:
                    s = arr_or_text.strip() or "_(none)_"
                return f"### {title}\n{s}\n"
            parts = [
                f"# Safety Plan for {pid}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
                lines("Warning signs", c.get("warning_signs", [])),
                lines("Internal coping strategies", c.get("internal_coping", [])),
                lines("People & places for distraction", c.get("distractions", [])),
                lines("Support contacts", [f"{r.get('name','')} ({r.get('relationship','')}) {r.get('phone','')}".strip()
                                           for r in c.get('support_contacts',[])]),
                lines("Professionals & agencies", [f"{r.get('service','')}: {r.get('name','')} {r.get('phone','')}".strip()
                                                   for r in c.get('professional_contacts',[])]),
                lines("Means restriction plan", c.get("means_restriction","")),
                lines("Reasons for living", c.get("reasons_for_living","")),
                lines("Crisis steps", c.get("crisis_steps", [])),
                lines("Environment safety", c.get("environment","")),
            ]
            return "\n".join(parts)
        md = to_md(selected)
        st.download_button("Download Markdown", data=md.encode("utf-8"),
                           file_name=f"{pid}_safety_plan_{selected['id']}.md",
                           mime="text/markdown", use_container_width=True)

        st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)
        st.subheader("Sharing")
        sh1, sh2 = st.columns(2)
        new_pt = sh1.toggle("Share with patient", value=bool(selected["shared"].get("patient", True)), key="share_pt")
        new_team = sh2.toggle("Share with care team", value=bool(selected["shared"].get("care_team", True)), key="share_team")
        if st.button("Update sharing"):
            sps.set_sharing(pid, selected_id, patient=new_pt, care_team=new_team)
            st.success("Sharing updated."); st.rerun()

        st.markdown("<div class='k-sep'></div>", unsafe_allow_html=True)
        a1, a2, a3 = st.columns(3)
        if a1.button("Duplicate to new version"):
            cloned = sps.update_new_version(pid, me, selected_id, selected["content"], keep_sharing=True)
            st.success(f"Created {cloned['id']} (v{cloned['version']})"); st.rerun()
        if a2.button("Delete this version"):
            if sps.delete(pid, selected_id):
                st.success("Deleted."); st.rerun()
        if a3.button("Set latest as active"):
            st.info("The newest version is considered active automatically.")

with left:
    st.subheader("Edit / Create")
    latest = sps.latest(pid)
    initial = latest["content"] if latest else None
    content = safety_plan_form_pro(initial=initial)

    b1, b2 = st.columns([1,1])
    if latest:
        if b1.button("Save as NEW version (recommended)", type="primary"):
            created = sps.update_new_version(pid, me, base_id=latest["id"], content=content, keep_sharing=False,
                                             shared_patient=content["shared"]["patient"], shared_care_team=content["shared"]["care_team"])
            st.success(f"Saved {created['id']} (v{created['version']})"); st.rerun()
        if b2.button("Overwrite latest (keep version number)"):
            created = sps.update_new_version(pid, me, base_id=latest["id"], content=content, keep_sharing=False,
                                             shared_patient=content["shared"]["patient"], shared_care_team=content["shared"]["care_team"])
            st.success(f"Saved {created['id']} (v{created['version']})"); st.rerun()
    else:
        if st.button("Create first safety plan", type="primary"):
            created = sps.create(pid, me, content, shared_patient=content["shared"]["patient"], shared_care_team=content["shared"]["care_team"])
            st.success(f"Saved {created['id']} (v1)"); st.rerun()
