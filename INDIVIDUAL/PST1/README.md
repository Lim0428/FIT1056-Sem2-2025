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



