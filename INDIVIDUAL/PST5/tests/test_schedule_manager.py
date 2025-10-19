# tests/test_schedule_manager.py
import pytest
import os
from app.schedule import ScheduleManager
from app.student import StudentUser

# A pytest fixture creates a clean environment for each test function.
@pytest.fixture
def fresh_manager():
    """Creates a fresh ScheduleManager instance using a temporary test data file."""
    test_file = "test_data.json"
    # ARRANGE: Ensure no old test file exists.
    if os.path.exists(test_file):
        os.remove(test_file)
    return ScheduleManager(data_path=test_file)

def test_create_course(fresh_manager):
    # ARRANGE: We have a fresh manager from the fixture.
    # ACT: Call the method we want to test.
    fresh_manager.create_course("Beginner Piano", "Piano", 1)
    # ASSERT: Check if the outcome is what we expect.
    assert len(fresh_manager.courses) == 1
    assert fresh_manager.courses[0].name == "Beginner Piano"

def test_record_payment_and_history(fresh_manager):
    # ARRANGE: Add a dummy student to the manager for the test.
    # This test verifies the core financial logic you added in Fragment 5.1.
    # fresh_manager.students.append(...)
    student_id_to_test = 1

    # ACT: Record a payment for that student.
    fresh_manager.record_payment(student_id_to_test, 100.00, "Credit Card")
    
    # ACT 2: Get the payment history.
    history = fresh_manager.get_payment_history(student_id_to_test)

    # ASSERT: Check the results.
    assert len(history) == 1
    assert history[0]['amount'] == 100.00
    assert history[0]['method'] == "Credit Card"
    
def test_get_payment_history_no_results(fresh_manager):
    """Ensure an empty list is returned when a student has no recorded payments."""
    # ARRANGE: Choose a student ID that has no payments
    student_id_without_payments = 999

    # ACT: Fetch history for a student with no payments
    history = fresh_manager.get_payment_history(student_id_without_payments)

    # ASSERT: It should be an empty list
    assert isinstance(history, list)
    assert history == []

def _make_course(mgr, name="Course 104", instrument="Violin", teacher_id=1):
    if hasattr(mgr, "create_course"):
        return mgr.create_course(name, instrument, teacher_id)
    return mgr.add_course(name, instrument, teacher_id)

def _lesson_id(lesson):
    # returns lesson_id from dict/object
    if isinstance(lesson, dict):
        return lesson.get("lesson_id") or lesson.get("id")
    return getattr(lesson, "lesson_id", getattr(lesson, "id", None))

def _get_lesson(course, lid):
    for L in getattr(course, "lessons", []):
        if _lesson_id(L) == lid:
            return L
    return None


def test_create_course_returns_expected_shape(fresh_manager):
    c = _make_course(fresh_manager, "Violin Performance and Technique", "Violin", teacher_id=7)
    assert c is not None
    assert getattr(c, "id", None) is not None
    assert getattr(c, "name", "") == "Violin Performance and Technique"
    assert getattr(c, "instrument", "") == "Violin"
    assert getattr(c, "teacher_id", None) == 7

def test_add_and_list_lesson(fresh_manager):
    c = _make_course(fresh_manager, "Course 101", "Piano", teacher_id=2)
    added = fresh_manager.add_lesson(c.id, "Monday", "13:00", "R1")
    lid = _lesson_id(added)
    assert lid is not None, "add_lesson must return lesson with lesson_id"

    # should be present in the same course.lessons
    c2 = fresh_manager.find_course_by_id(c.id)
    found = _get_lesson(c2, lid)
    assert found is not None
    # spot-check fields
    if isinstance(found, dict):
        assert found["day"] == "Monday"
        assert found["start_time"] == "13:00"
        assert found["room"] == "R1"
    else:
        assert found.day == "Monday"
        assert found.start_time == "13:00"
        assert found.room == "R1"

def test_cancel_lesson_sets_cancelled_flag_true(fresh_manager):
    c = _make_course(fresh_manager, "Course 104", "Violin", teacher_id=3)
    added = fresh_manager.add_lesson(c.id, "Tuesday", "10:30", "A2")
    lid = _lesson_id(added)

    ok = fresh_manager.cancel_lesson(c.id, lid, "Student sick")
    assert ok is True

    c_after = fresh_manager.find_course_by_id(c.id)
    L = _get_lesson(c_after, lid)
    assert L is not None
    cancelled = (L["cancelled"] if isinstance(L, dict) else getattr(L, "cancelled", None))
    assert cancelled is True

def test_reschedule_lesson_updates_fields(fresh_manager):
    c = _make_course(fresh_manager, "Piano 201", "Piano", teacher_id=4)
    added = fresh_manager.add_lesson(c.id, "Wednesday", "09:00", "B1")
    lid = _lesson_id(added)

    fresh_manager.reschedule_lesson(c.id, lid, "Thursday", "11:15", "B3")

    c_after = fresh_manager.find_course_by_id(c.id)
    L = _get_lesson(c_after, lid)
    assert L is not None
    if isinstance(L, dict):
        assert L["day"] == "Thursday"
        assert L["start_time"] == "11:15"
        assert L["room"] == "B3"
    else:
        assert L.day == "Thursday"
        assert L.start_time == "11:15"
        assert L.room == "B3"
