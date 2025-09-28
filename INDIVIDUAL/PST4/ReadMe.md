# Music School Management System (MSMS v4) – PST4

**MSMS v4** is an enhanced version of the Music School Management System, designed to provide a **user-friendly, interactive GUI** for managing students, teachers, courses, lessons, attendance, feedback, grades, and payments using **Streamlit**.

The system covers management of:

* Courses
* Lessons
* Enrollment and unenrollment
* Attendance and check-in
* Feedback
* Grades
* Payments and finance
* Scheduling

## User Capabilities

### **Students**

* **Check in for lessons** to mark attendance for enrolled courses.
* **Submit feedback** for their courses.
* **View grades** with optional notes from teachers.

### **Teachers**

* **View assigned courses**.
* **View student attendance records**.
* **View feedback submitted by students**.
* **View and assign grades** to students with optional notes.

### **Receptionists / Admin**

* **Enroll students** in courses.
* **Unenroll students** from courses.
* **Record and update student payments or balances**.
* **View attendance summary** for students and courses.
* **Generate finance reports**: Outstanding balances and payment histories.
* **List overview** of students, teachers, and courses.

### **Schedule Management**

* **Switch courses** for students.
* **Cancel lessons**.
* **Reschedule lessons** with automatic conflict checking (room, teacher, student).

## Key Enhancements in PST4

* **Streamlit GUI**: Fully interactive dashboard with buttons, forms, and tables.
* **Enroll/Unenroll Functionality**: One page handles both enrollment and removal of students.
* **Daily Roster**: Visual daily schedule with real-time check-in functionality.
* **Conflict Checking**: Prevent overlapping lessons and room/teacher conflicts.
* **JSON Persistence**: Data for students, teachers, courses, attendance, feedback, grades, and lesson changes is saved and loaded automatically.
* **Timestamps**: Attendance, payments, feedback, and grades are recorded with timestamps.
* **Input Validation**: Ensures correct IDs and prevents duplicate enrollments.

## Object-Oriented Design

1. **User**: Base class storing `ID` and `name`.
2. **StudentUser**: Inherits from `User`, stores enrolled courses, balance, and payment history.
3. **TeacherUser**: Inherits from `User`, stores teacher’s specialty.
4. **Course**: Stores course information, lessons, enrolled students, teacher ID, and fees.
5. **ScheduleManager**: Core controller managing all operations, GUI interactions, persistence, and conflict checking.

## Key Methods

* **_load_data() / _save_data()**: Handles JSON persistence.
* **enroll_student(), unenroll_student()**: Manage course enrollment.
* **check_in()**: Record student attendance.
* **submit_feedback(), assign_grade()**: Handle feedback and grading.
* **cancel_lesson(), reschedule_lesson()**: Manage lessons and conflicts.
* **attendance_report(), finance_report()**: Generate student, course, and financial reports.
* **record_payment()**: Update payments and balances.
* **add_course(), add_lesson()**: Add new courses and lessons.

## Directory Structure

```
msms/
├─ app/
│  ├─ student.py
│  ├─ teacher.py
│  └─ schedule.py
├─ gui/
│  ├─ main_dashboard.py
│  ├─ student_pages.py
│  ├─ roster_pages.py
│  ├─ enroll_page.py
│  ├─ course_page.py
│  ├─ teacher_page.py
│  ├─ attendance_pages.py
│  ├─ payment_pages.py
│  ├─ grade_pages.py
│  ├─ feedback_pages.py
│  └─ lesson_pages.py
├─ data/
│  └─ msms.json
├─ main.py
└─ ReadMe.md
```

4. Navigate the dashboard to manage students, teachers, courses, attendance, feedback, grades, and payments.

## Notes

* Data is stored in `msms.json` for persistence.
* Enrollment options are filtered so students can only enroll in courses they are not already enrolled in.
* The roster and check-in pages only show lessons relevant to the selected day.
* GUI ensures unique widget IDs to prevent Streamlit duplicate element errors.

---

**MSMS v4** provides a clean, interactive experience for managing all aspects of a music school efficiently and accurately.
