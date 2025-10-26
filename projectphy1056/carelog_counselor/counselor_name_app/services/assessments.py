# counselor_name_app/services/assessments.py
from __future__ import annotations
from typing import Dict, List, Optional
from counselor_name_app.repository import Repo

# -----------------------------
# Scoring thresholds & guidance
# -----------------------------
PHQ9_BANDS = [
    (0, 4,  "Minimal",           "No or minimal depressive symptoms."),
    (5, 9,  "Mild",              "Consider watchful waiting; repeat screening."),
    (10,14, "Moderate",          "Consider counseling; develop treatment plan."),
    (15,19, "Moderately Severe", "Active treatment with psychotherapy +/- medication."),
    (20,27, "Severe",            "Immediate treatment; consider urgent evaluation.")
]

GAD7_BANDS = [
    (0, 4,  "Minimal",  "No or minimal anxiety symptoms."),
    (5, 9,  "Mild",     "Consider watchful waiting; repeat screening."),
    (10,14, "Moderate", "Consider counseling; develop treatment plan."),
    (15,21, "Severe",   "Active treatment; consider urgent evaluation.")
]

def _band(score: int, table: List[tuple]) -> tuple[str,str]:
    for lo, hi, label, msg in table:
        if lo <= score <= hi:
            return label, msg
    return "—", "—"

# severity → a simple tag for styling
SEVERITY_LEVEL = {
    "Minimal": "ok",
    "Mild": "ok",
    "Moderate": "warn",
    "Moderately Severe": "warn",
    "Severe": "bad",
}

PHQ9_ITEMS = 9
GAD7_ITEMS = 7

class AssessmentService:
    def __init__(self, repo: Optional[Repo]=None):
        self.repo = repo or Repo()

    # ---- scoring helpers ----
    def score_phq9(self, answers: List[int]) -> Dict:
        total = sum(answers[:PHQ9_ITEMS])
        band, guidance = _band(total, PHQ9_BANDS)
        return {"tool":"PHQ-9","score": total, "band": band, "severity": SEVERITY_LEVEL.get(band,"ok"),
                "guidance": guidance}

    def score_gad7(self, answers: List[int]) -> Dict:
        total = sum(answers[:GAD7_ITEMS])
        band, guidance = _band(total, GAD7_BANDS)
        return {"tool":"GAD-7","score": total, "band": band, "severity": SEVERITY_LEVEL.get(band,"ok"),
                "guidance": guidance}

    # ---- persistence ----
    def save(self, patient_id: str, counselor_id: str, result: Dict):
        db = self.repo.read()
        db.setdefault("assessments", {}).setdefault(patient_id, []).append({
            **result, "by": counselor_id
        })
        self.repo.write(db)

    def list_for_patient(self, patient_id: str) -> List[Dict]:
        return self.repo.read().get("assessments", {}).get(patient_id, [])
