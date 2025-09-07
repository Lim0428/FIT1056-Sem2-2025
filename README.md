<<<<<<< HEAD

----Music School Management System (MSMS)----PRT1

----Overview----
PST1 is a in-memory prototype Music School Management System that designed for the school's stuff or admin to do the following:
1.register new students
2.enrol existing students in more instruments
3.register new teachers
4.lookup for students or teachers
5.list all students or teachers 


Structure:
DATA
1.Student 
-with unique ID
-with name
-enrolled instruments

2.Teacher
-with unique ID
-with name
-speciality

In-memory databases
student_db - lists of all students
teacher_db - lists of all teachers
next_()_id - count for unique teachers/students ID

3.Function
add_students(name,instrument) - add and enroll students in the system
enrol_student(student_id,instrument) - add instruments for existing student
add_teacher(name,speciality) - register new teachers
lookup_student/teacher - search teacher or student by the information
list_all_(student/teacher) - display student and teacher

4.Menu
main() function to start the program


Testing !!!
1.Register new student
  -select 1 in menu
  -enter student name and instrument
  -can type x to exit 

2.Enroll existing student
  -select 2 in menu
  -enter valid ID
  -enter instrument
  -can type x to exit

3.Register new teacher
  -select 3
  -enter teacher name and speciality
  -can type x to exit

4.Lookup teacher/student
  -select 4
  -enter information

5.List all students/teachers
  -admin used to see student/teacher list

Design
In-memory storage means program resets each run
type "x" as shortcut to return back menu
student and teacher ID increase automatically



PST2

This is a console application to manage student,courses, teacher in a music school
It is in-memory data storage

Devide to student and teacher options
Can show amount of student and teacher

Import json
-can save data in other file,load data from other file

Student management
-the program can add and remove student
-random student selector
-can rename student

Teacher management
-the program can add and remove teachers
-can update teacher details

Easy used menu
-can access all feature via simple key in number
origin/individual

=======
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
>>>>>>> 8282bed (First commit to PST 3)
