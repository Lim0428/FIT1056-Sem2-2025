# tests/test_scheduling_helpers.py
from datetime import date, time, datetime, timedelta

from admin_name_ui.scheduling import (
    _fmt_time_iso, _parse_iso, _overlap,
    _user_availability_ok, _conflicts_for, _next_appt_id, WEEK_DAYS
)

def test_fmt_parse_roundtrip():
    d = date(2025, 5, 20)
    t = time(9, 30)
    iso = _fmt_time_iso(d, t)
    dt = _parse_iso(iso)
    assert dt.year == 2025 and dt.month == 5 and dt.day == 20
    assert dt.hour == 9 and dt.minute == 30

def test_overlap_basic():
    s1, e1 = datetime(2025,1,1,9),  datetime(2025,1,1,10)
    s2, e2 = datetime(2025,1,1,9,30), datetime(2025,1,1,10,30)
    assert _overlap(s1, e1, s2, e2) is True
    # touching at boundary is not overlap
    s3, e3 = datetime(2025,1,1,10), datetime(2025,1,1,11)
    assert _overlap(s1, e1, s3, e3) is False

def test_user_availability_ok_within_and_outside():
    # Available Mon 09-17
    user = {"role":"doctor", "availability":[{"day":"Mon","start":"09:00","end":"17:00"}]}
    # Monday 10:00-11:00 -> ok
    d = date(2025, 5, 19) # Monday
    ok, reason = _user_availability_ok(user, d, time(10,0), time(11,0))
    assert ok and reason == ""
    # Monday 08:00-09:00 -> outside
    ok, reason = _user_availability_ok(user, d, time(8,0), time(9,0))
    assert not ok and "outside" in reason.lower()

def test_conflicts_for_doctor_patient_nurse_room(fake_db):
    db = fake_db
    # seed entities
    db["patients"] = [{"id": 1, "name":"P"}]
    db["users"] = [
        {"id": 2, "name":"D", "role":"doctor"},
        {"id": 3, "name":"N", "role":"nurse"},
    ]
    db["rooms"] = [{"id": 10, "code":"RM1"}]

    s = _fmt_time_iso(date(2025,5,20), time(9,0))
    e = _fmt_time_iso(date(2025,5,20), time(10,0))
    db["appointments"] = [{
        "id": 1, "patient_id":1, "doctor_id":2, "nurse_id":3, "room_id":10,
        "start_iso": s, "end_iso": e, "status":"booked"
    }]

    s_dt = _parse_iso(_fmt_time_iso(date(2025,5,20), time(9,30)))
    e_dt = _parse_iso(_fmt_time_iso(date(2025,5,20), time(10,30)))

    assert _conflicts_for(db, "doctor", 2, s_dt, e_dt)  # overlaps
    assert _conflicts_for(db, "patient", 1, s_dt, e_dt)
    assert _conflicts_for(db, "nurse", 3, s_dt, e_dt)
    assert _conflicts_for(db, "room", 10, s_dt, e_dt)

def test_next_appt_id(fake_db):
    db = fake_db
    db["appointments"] = [{"id":5}, {"id":7}]
    assert _next_appt_id(db) == 8
