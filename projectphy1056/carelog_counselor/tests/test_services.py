# tests/test_services.py
from datetime import datetime, timedelta
import pytest

from counselor_name_app.repository import Repo
from counselor_name_app.services.identity import IdentityService
from counselor_name_app.services.consent import ConsentService
from counselor_name_app.services.patients import PatientService
from counselor_name_app.services.notes import NotesService
from counselor_name_app.services.assessments import AssessmentService
from counselor_name_app.services.messaging import MessagingService

# Your codebase defines AppointmentService twice; the final one uses dateutil.
pytest.importorskip("dateutil.parser")
from counselor_name_app.services.appointments import AppointmentService


def test_repository_seeds(tmp_repo: Repo):
    db = tmp_repo.read()
    assert "users" in db and "patients" in db and "messages" in db
    assert "C0001" in db["users"]
    assert "P0001" in db["patients"]


def test_identity_login_and_lockout(tmp_repo: Repo, ids):
    svc = IdentityService(tmp_repo)
    ok = svc.login(ids["counselor"], "password123")
    assert ok and ok["id"] == ids["counselor"]

    assert svc.login(ids["counselor"], "bad") is None
    assert svc.login(ids["counselor"], "bad") is None
    assert svc.login(ids["counselor"], "bad") is None

    assert svc.login(ids["counselor"], "password123") is None  # locked

    svc.reset_lock(ids["counselor"])
    ok2 = svc.login(ids["counselor"], "password123")
    assert ok2 and ok2["id"] == ids["counselor"]


def test_consent_allowed_and_break_glass(tmp_repo: Repo, ids):
    consent = ConsentService(tmp_repo)
    assert consent.allowed(ids["counselor"], ids["patient"]) is True

    other = "C9999"
    db = tmp_repo.read()
    db.setdefault("users", {})[other] = {"id": other, "name": "Temp", "password": "x"}
    tmp_repo.write(db)

    assert consent.allowed(other, ids["patient"]) is False
    assert consent.break_glass(other, ids["patient"], reason="Emergency cover") is True
    assert consent.allowed(other, ids["patient"]) is True


def test_patients_list_assigned(tmp_repo: Repo, ids):
    ps = PatientService(tmp_repo)
    assigned = ps.list_assigned(ids["counselor"])
    assert any(p["id"] == ids["patient"] for p in assigned)


def test_notes_create_and_list(tmp_repo: Repo, ids):
    ns = NotesService(tmp_repo)
    note = ns.create(
        patient_id=ids["patient"],
        counselor_id=ids["counselor"],
        template="SOAP",
        title="Therapy session",
        content={"Subjective":"ok","Objective":"stable","Assessment":"mild","Plan":"CBT"}
    )
    assert note["id"].startswith("N-")
    notes = ns.list_notes(ids["patient"])
    assert any(n["id"] == note["id"] for n in notes)


def test_assessments_score_and_save(tmp_repo: Repo, ids):
    asv = AssessmentService(tmp_repo)
    phq = asv.score_phq9([3]*9)
    assert phq["tool"] == "PHQ-9" and phq["score"] == 27

    asv.save(ids["patient"], ids["counselor"], phq)
    assert any(r["tool"] == "PHQ-9" for r in asv.list_for_patient(ids["patient"]))

    gad = asv.score_gad7([2]*7)
    asv.save(ids["patient"], ids["counselor"], gad)
    assert any(r["tool"] == "GAD-7" for r in asv.list_for_patient(ids["patient"]))


def test_appointments_booking_and_conflict(tmp_repo: Repo, ids):
    aps = AppointmentService(tmp_repo)

    start = (datetime.now().replace(microsecond=0) + timedelta(hours=2))
    end = start + timedelta(hours=1)
    ap = aps.book(ids["patient"], ids["counselor"], start.isoformat(), end.isoformat(), "Individual")
    assert ap["id"].startswith("A-")

    with pytest.raises(ValueError):
        aps.book(ids["patient"], ids["counselor"],
                 (start + timedelta(minutes=15)).isoformat(),
                 (end + timedelta(minutes=15)).isoformat(),
                 "Follow-up")

    start2 = end + timedelta(minutes=1)
    end2 = start2 + timedelta(hours=1)
    ap2 = aps.book(ids["patient"], ids["counselor"], start2.isoformat(), end2.isoformat(), "Follow-up")
    assert ap2["id"].startswith("A-")


def test_messaging_post_and_crisis_autoreply(tmp_repo: Repo, ids):
    ms = MessagingService(tmp_repo)
    out = ms.post(None, [ids["counselor"], ids["patient"]], ids["counselor"], "Hello there")
    tid = out["thread_id"]
    t = next(t for t in ms.list_threads(ids["counselor"]) if t["id"] == tid)
    assert len(t["items"]) == 1

    ms.post(tid, [ids["counselor"], ids["patient"]], ids["patient"], "I might overdose if this continues")
    t2 = next(t for t in ms.list_threads(ids["counselor"]) if t["id"] == tid)
    assert len(t2["items"]) == 3
    assert any(m["by"] == "system" for m in t2["items"])

    audit = tmp_repo.read().get("audit", [])
    assert any(a.get("event") == "crisis_escalation" and a.get("thread") == tid for a in audit)
