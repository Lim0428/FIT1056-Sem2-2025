# Music School Management System (MSMS v3) – PST3

My **Music School Management System (MSMS)** is design for four users
1.**students**
2.**teachers**
3.**receptionists**
4.**schedule manager**

The system cover the **function** such as manage
-course
-lesson
-enrollment
-attendance
-feedback
-grades
-payment
-scheduling

This version have enhance functionalities

For **student**, the system allow
-**check in lesson** so student can mark attendance for their enrolled course
-**submit feedback** for their course
-**view grade** assigned by teachers with optional notes
-**view student** enrolled courses 

For **teacher**, the system allow
-**view assigned courses**
-**view attendance**
-**view feedback** from students
-**view student grade**
-**assigned grade** to student with optional notes

For **receptionist**, the system allow
-**enroll students** in courses
-**record and update student payment** or balance
-**view attendance summary** for student and course
-**Finance Reports**: View outstanding balances and payment histories.
-**list** student/ teacher /course overview

For Schedule Manager, the system allow to
-**switch** course for student
-**cancel lesson** 
-**reschedule lesson** for checking room,teacher or student conflict

In this PST3, the program have a **clean menu**. To avoid to many options in the main menu, program devided to **4 main roles**, including **student, teacher, schedule manager and receptionist**. The data is stored in **json file** and supports student, teacher, lesson changes, attendance and feedback also the grade.Data can loaded and save successfully.The program have the **basic input validation and conflict checking for lessons**. It can prevent room, teacher and student conflicts.

Key Enhancement
-**Roled based menu**
Each user role has a clean, context-specific menu to simplify operations

-**JSON Data Persistence**
upports saving and loading of students, teachers, courses, attendance, feedback, grades, and lesson changes

-**Timestamps**
Attendance, payments, feedback, and grades are recorded with timestamps



# Object-oriented design
1. **User**: Base class storing `ID` and `name`.  
2. **StudentUser**: Inherits from `User`, stores enrolled courses, balance, and payment history.  
3. **TeacherUser**: Inherits from `User`, stores teacher’s specialty.  
4. **Course**: Stores course information, lessons, enrolled students, teacher ID, and fees.  
5. **ScheduleManager**: Core system controller managing all operations, persistence, and conflict checking.  


**Methods**
-**_load_data(),_save_data()** can handle JSON persistence
-**check_in()** allow record attendance with timestamp
-**enroll_student(), switch_course()** can manage student course
-**cancel_lesson(), reschedule_lesson()** used for lesson management
-**submit_feedback(), assign_grade()** in program can submit feedback and assign grade
-**attendance_report()/ finance_report()** that can generate reports for students, courses, and finances.
-**record_payment()** can update student payment and balance.



## How to Run
1. Ensure **Python 3.x** is installed.  
2. Place `msms.json` in the same folder (optional; the system will start empty if not found).  
3. Run the program:

```bash
python msms.py
