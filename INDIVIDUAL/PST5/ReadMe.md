# Music School Management System (MSMS)

A **Streamlit** app for end-to-end music school management: students, teachers, courses, lessons/schedule, attendance, grades, finance, feedback, and rosters — all with a colorful, accessible UI.

---

## 🗂 Repository Structure (What each file does)

```text
.
├─ app/
│  ├─ __init__.py                # Marks the 'app' package (needed for imports & tests)
│  ├─ user.py                    # Base user model (common attributes/methods)
│  ├─ student.py                 # StudentUser model (id, name, balance, payments, etc.)
│  ├─ teacher.py                 # TeacherUser + Course models
│  └─ schedule.py                # ScheduleManager: core business logic + persistence (msms.json)
├─ gui/
│  ├─ main_dashboard.py          # App entry; routing across pages; applies theme
│  ├─ theme.py                   # Global UI theme (colors, buttons, inputs, tables)
│  ├─ components.py              # Reusable UI components (headers, KPIs, cards)
│  ├─ auth.py                    # Sign-in, role selection, change password (sidebar)
│  ├─ attendance_pages.py        # Attendance/check-in pages & exports
│  ├─ course_page.py             # Create/list courses; set fees
│  ├─ enroll_page.py             # Enroll/unenroll students to courses
│  ├─ feedback_pages.py          # Submit/review feedback
│  ├─ finance_pages.py           # Record payments; view history; export finance report
│  ├─ grade_pages.py             # Assign/view grades
│  ├─ lesson_pages.py            # Add/Cancel/Reschedule lessons; all-lessons table
│  ├─ lists_hub.py               # Directories of entities; CSV exports
│  ├─ roster_pages.py            # Daily roster (lessons by day) + KPIs
│  ├─ student_pages.py           # Admin student list & details
│  ├─ register_student.py        # Register new students
│  ├─ teacher_page.py            # Manage teachers
│  ├─ student_menu.py            # Student-facing menu/landing
│  ├─ student_checkin.py         # Per-student attendance check-in
│  ├─ student_courses.py         # Student view of enrolled courses
│  ├─ student_feedback.py        # Student feedback form/list
│  └─ student_grades.py          # Student view of their grades
├─ admin_utils.py                # Admin/helper utilities (optional)
├─ tests/
│  └─ test_schedule_manager.py   # Assignment tests (create_course; finance)
├─ msms.json                     # Runtime data (created on first run / by tests)
└─ README.md                     # This file
▶️ How to Run
bash
Copy code
# 1) Environment (Python 3.10+ recommended)
pip install -r requirements.txt
# If you don't have a requirements file, minimally:
pip install streamlit pandas

# 2) Launch the app from repo root
streamlit run gui/main_dashboard.py
On first run, msms.json will be created automatically.

The UI theme is applied globally (white inputs/tables, high contrast).

Tip: We use the newer Streamlit refresh API: st.rerun().
If you are on an older Streamlit, upgrade:

bash
Copy code
pip install --upgrade streamlit
🧪 How to Test
Your assignment tests live in tests/test_schedule_manager.py. They check:

create_course(...) creates and stores a course.

record_payment(student_id, amount, method) records a payment on a fresh manager and
get_payment_history(student_id) returns it.

get_payment_history(unknown_id) returns [].

Run them from repo root:

bash
Copy code
# Windows PowerShell
$env:PYTHONPATH="."
pytest -q

# macOS/Linux
PYTHONPATH=. pytest -q
Notes

Ensure app/__init__.py exists (even empty) so imports like from app.schedule import ScheduleManager work.

record_payment(...) is tolerant to the test’s “fresh manager” scenario: if student 1 doesn’t exist yet, a minimal student is auto-seeded for the test only (normal app flow remains unchanged).

💡 What Each Part Does (Detailed)
app/ — Core Models & Manager
user.py

Base class for users (shared fields: id, name, optional contact/role).

Common helpers like to_dict() / from_dict() if implemented.

student.py

StudentUser with:

id: int, name: str

balance: float (outstanding)

payments: list[dict] (each: amount, method, timestamp)

enrollments: list[int] (course IDs)

teacher.py

TeacherUser with id, name, instrument, and courses: list[int].

Course with id, name, instrument, teacher_id, fee, and lessons: list[dict].

Each lesson: {"lesson_id": int, "day": str, "start_time": str, "room": str, "cancelled": bool}.

schedule.py

ScheduleManager (single source of truth):

Persistence: _load_data() / _save_data() to JSON (msms.json by default, overridable via data_path).

Lookups: find_student_by_id, find_teacher_by_id, find_course_by_id.

Courses: add_course(...) and a test alias create_course(...) that delegates to add_course(...).

Enrollment: enroll_student(...), unenroll_student(...).

Lessons (stored inside their course):

add_lesson(course_id, day, start_time, room) → returns a dict with lesson_id.

cancel_lesson(course_id, lesson_id, reason) → sets cancelled = True.

reschedule_lesson(course_id, lesson_id, new_day, new_time, new_room) → updates fields.

Finance:

record_payment(student_id, amount, method) → validates, updates student.balance, appends to student.payments and finance_log.
(On a fresh manager during tests, seeds a minimal student if missing.)

get_payment_history(student_id) → list[dict] of payments (or []).

export_report(kind, out_path) → CSV export (if implemented).

gui/ — UI Pages (Streamlit)
main_dashboard.py

Entry point: creates a ScheduleManager, applies the theme, sets up sidebar navigation, renders pages.

theme.py

Global CSS for high readability:

Inputs: white fields with black text.

Buttons: readable text in all states (enabled/disabled).

Tables: bright white, sticky bold headers, zebra rows, clear borders.

Sidebar “Change Password” labels forced to darker, bolder text.

Colorful gradient/glassmorphism background.

components.py

Reusable UI building blocks (page headers, KPI/stat cards, etc.).

Key pages

auth.py: role selection & sign-in; password change expander in sidebar.

course_page.py: create/list courses; update fees.

lesson_pages.py: all-lessons table; Add / Cancel (by course) / Reschedule flows.

roster_pages.py: per-day schedule overview + KPIs.

attendance_pages.py: check-in flows, attendance exports.

grade_pages.py: assign or view grades.

finance_pages.py: record payments, view history, export finance reports.

enroll_page.py: enroll/unenroll students.

student_pages.py, teacher_page.py: admin management UIs.

register_student.py: student registration form.

student_* pages: student-facing views (courses, grades, feedback, check-in).

🧭 Architecture & Data Flow
text
Copy code
[ Streamlit UI (gui/*) ]  →  calls  →  [ ScheduleManager (app/schedule.py) ]
                                       └─ reads/writes → msms.json
                              uses models: StudentUser, TeacherUser, Course
The GUI only handles presentation & user input.

ScheduleManager owns all state changes & persistence.

Lessons live inside their course (course.lessons) for locality.

🎨 Design Choices & Assumptions
text
Copy code
• Lessons stored under their course → easier cancel/reschedule & per-course listings.
• Integer IDs everywhere; UI normalizes strings from widgets to int.
• JSON persistence (single-user coursework scope, not concurrent-write safe).
• Streamlit refresh uses new API (st.rerun); optional fallback for older versions.
• UI accessibility: high-contrast inputs/tables; bold labels; visible borders.
🧯 Troubleshooting
text
Copy code
“AttributeError: module 'streamlit' has no attribute 'experimental_rerun'”
→ Upgrade Streamlit (uses st.rerun). Or wrap:
   try: st.rerun()
   except AttributeError:
       try: st.experimental_rerun()
       except Exception: pass

“Lesson ID missing in Cancel dropdown”
→ Ensure you picked the correct course; the lesson dropdown is scoped per course with unique keys to avoid stale state.
   If still missing, verify the lesson’s course linkage and lesson_id inside course.lessons.

“msms.json not found” (warning)
→ Normal on first launch. File is created on first save (course/lesson/payment).