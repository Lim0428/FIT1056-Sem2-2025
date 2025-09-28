import json, datetime, os
# import json used to read/write JSON files for persistent storage
# import datetime used for timestamps (e.g., attendance, grades, payments)
# import os used to check if the JSON data file exist

# base class for user(student, teacher) to store ID and name
class User:
    def __init__(self, user_id, name):
        self.id = int(user_id)
        self.name = name

# inherit from user class to add enroll course, balance and payment
class StudentUser(User):
    def __init__(self, user_id, name):
        super().__init__(user_id, name)
        self.enrolled_course_ids = []   #list of enroll course ID
        self.balance = 0.0   #outstanding balance
        self.payments = []   #list of payment

# teacher class with id, name and speciality
class TeacherUser(User):
    def __init__(self, user_id, name, speciality):
        super().__init__(user_id, name)
        self.speciality = speciality

# course class to track students, leeson and fee they paid
class Course:
    def __init__(self, course_id, name, instrument, teacher_id, fee=0.0):
        self.id = int(course_id)
        self.name = name
        self.instrument = instrument
        self.teacher_id = int(teacher_id)
        self.enrolled_student_ids = []
        self.lessons = []  
        self.fee = float(fee)

# core system manager to track student, teacher, courses, attendance logs, feedback by 
# student/teacher, student grade, lesson cancellations and reschedules
class ScheduleManager:
    def __init__(self, data_path="msms.json"):
        self.data_path = data_path
        self.students, self.teachers, self.courses = [], [], []
        self.attendance_log, self.feedbacks, self.grades, self.lesson_changes = [], [], [], []
        self._load_data()

   # function that load data from json
    def _load_data(self):
        #system will starts empty when file is not exist
        if not os.path.exists(self.data_path):
            print("Warning: msms.json not found, starting empty.")
            return
        with open(self.data_path, 'r') as f:
            data = json.load(f)
        # Students
        self.students = []
        for s in data.get("students", []):
            st = StudentUser(s.get("id"), s.get("name"))
            st.enrolled_course_ids = s.get("enrolled_course_ids", [])
            st.balance = s.get("balance",0.0)
            st.payments = s.get("payments",[])
            self.students.append(st)
        # Teachers
        self.teachers = []
        for t in data.get("teachers", []):
            th = TeacherUser(t.get("id"), t.get("name"), t.get("speciality","Unknown"))
            self.teachers.append(th)
        # Courses
        self.courses = []
        for c in data.get("courses", []):
            co = Course(c.get("id"), c.get("name"), c.get("instrument"), c.get("teacher_id"), c.get("fee",0.0))
            co.enrolled_student_ids = c.get("enrolled_student_ids", [])
            lessons=[]
            for L in c.get("lessons", []):
                lessons.append({
                    "lesson_id": L.get("lesson_id"),
                    "day": L.get("day"),
                    "start_time": L.get("start_time"),
                    "room": L.get("room","TBD"),
                    "cancelled": L.get("cancelled",False)
                })
            co.lessons = lessons
            self.courses.append(co)
        self.attendance_log = data.get("attendance",[])
        self.feedbacks = data.get("feedbacks",[])
        self.grades = data.get("grades",[])
        self.lesson_changes = data.get("lesson_changes",[])

    # print lists for student, teacher and course
    def list_students(self):
        for s in self.students:
            print(f"{s.id}: {s.name} | Balance: {s.balance:.2f}")

    def list_teachers(self):
        for t in self.teachers:
            print(f"{t.id}: {t.name} ({t.speciality})")

    def list_courses(self):
        for c in self.courses:
            t = self.find_teacher_by_id(c.teacher_id)
            print(f"{c.id}: {c.name} [{c.instrument}] - Teacher: {t.name if t else 'Unknown'} - Fee: {c.fee:.2f}")

    # count the attendance per student per course
    def attendance_report(self):
            print("\n--- Attendance Report ---")
            if not self.attendance_log:
                print("No attendance records.")
                return
            report = {}
            for a in self.attendance_log:
                s = self.find_student_by_id(a["student_id"])
                c = self.find_course_by_id(a["course_id"])
                if not (s and c):
                    continue
                key = (s.name, c.name)
                report[key] = report.get(key, 0) + 1
            for (stu, cou), count in report.items():
                print(f"{stu} -> {cou}: {count}")

    # show balance per student and total outstandings
    def finance_report(self):
        print("\n--- Finance Report ---")
        total = 0.0
        for s in self.students:
            print(f"{s.id}: {s.name} - Balance {s.balance:.2f} - Payments {len(s.payments)}")
            total += s.balance
        print(f"TOTAL OUTSTANDING: {total:.2f}")

    # verifies valid teacher, student, and course and checks if the teacher is actually assigned to the course
    def assign_grade(self, teacher_id, student_id, course_id, grade, note=""):
        teacher = self.find_teacher_by_id(teacher_id)
        student = self.find_student_by_id(student_id)
        course = self.find_course_by_id(course_id)
        if not (teacher and student and course):
            print("Invalid teacher/student/course ID.")
            return False
        if course.teacher_id != teacher.id:
            print("Permission denied: You are not assigned to this course.")
            return False
        ts = datetime.datetime.now().isoformat()
        g = {"teacher_id": teacher.id, "student_id": student.id, "course_id": course.id, "grade": grade, "note": note, "timestamp": ts}
        self.grades.append(g)
        self._save_data()
        print(f"Grade assigned: {student.name} -> {course.name}: {grade}")
        return True

    # saves everything into msms.json with proper indentation
    def _save_data(self):
        # __dict__ let object become dictionaries
        data = {
            "students":[s.__dict__ for s in self.students],
            "teachers":[t.__dict__ for t in self.teachers],
            "courses":[c.__dict__ for c in self.courses],
            "attendance":self.attendance_log,
            "feedbacks":self.feedbacks,
            "grades":self.grades,
            "lesson_changes":self.lesson_changes
        }
        with open(self.data_path,'w') as f:
            json.dump(data, f, indent=4)

    # find stutend/ teacher and course by id
    def find_student_by_id(self,sid):
        return next((s for s in self.students if s.id==sid), None)
    def find_teacher_by_id(self,tid):
        return next((t for t in self.teachers if t.id==tid), None)
    def find_course_by_id(self,cid):
        return next((c for c in self.courses if c.id==cid), None)

    # records student that attend the course with timestamp
    def check_in(self,student_id,course_id):
        student=self.find_student_by_id(student_id)
        course=self.find_course_by_id(course_id)
        if not student or not course:
            print("Invalid Student or Course ID.")
            return
        ts=datetime.datetime.now().isoformat()
        self.attendance_log.append({"student_id":student.id, "course_id":course.id, "timestamp":ts})
        self._save_data()
        print(f"{student.name} checked in to {course.name}.")

    # enroll student to course and updates course’s enrolled list and student balance
    def enroll_student(self,student_id,course_id):
        student=self.find_student_by_id(student_id)
        course=self.find_course_by_id(course_id)
        if not student or not course: return
        if course.id in student.enrolled_course_ids:
            print("Already enrolled.")
            return
        student.enrolled_course_ids.append(course.id)
        course.enrolled_student_ids.append(student.id)
        student.balance += course.fee
        self._save_data()
        print(f"{student.name} enrolled to {course.name}. Fee: {course.fee}")

    # moves a student from one course to another while keeping data consisten
    def switch_course(self,student_id,from_cid,to_cid):
        student=self.find_student_by_id(student_id)
        from_course=self.find_course_by_id(from_cid)
        to_course=self.find_course_by_id(to_cid)
        if not student or not from_course or not to_course: return
        if from_cid not in student.enrolled_course_ids:
            print("Student not enrolled in the original course.")
            return
        student.enrolled_course_ids.remove(from_cid)
        if student.id in from_course.enrolled_student_ids:
            from_course.enrolled_student_ids.remove(student.id)
        self.enroll_student(student.id,to_course.id)

    # function to update course fee
    def set_course_fee(self,cid,fee):
        course=self.find_course_by_id(cid)
        if not course: return
        course.fee=float(fee)
        self._save_data()
        print(f"{course.name} fee set to {course.fee}")

    # function to record payment and update balance
    def record_payment(self,sid,amount,note=""):
        student=self.find_student_by_id(sid)
        if not student: return
        student.payments.append({"amount":amount,"timestamp":datetime.datetime.now().isoformat(),"note":note})
        student.balance-=amount
        self._save_data()
        print(f"{student.name} paid {amount}. New balance: {student.balance}")

    # submit feedback to the course
    def submit_feedback(self,sid,cid,comment):
        student=self.find_student_by_id(sid)
        course=self.find_course_by_id(cid)
        if not student or not course: return
        fb={"student_id":sid,"course_id":cid,"comment":comment,"timestamp":datetime.datetime.now().isoformat()}
        self.feedbacks.append(fb)
        self._save_data()
        print(f"Feedback submitted for {course.name} by {student.name}")

    # checks whether two lessons occur in the same time slot
    # @staticmethod, a utility function for comparing lesson slots
    @staticmethod
    def _same_slot(day_a,time_a,day_b,time_b):
        return str(day_a).strip().lower()==str(day_b).strip().lower() and str(time_a).strip()==str(time_b).strip()

    # marks lesson as cancelled
    def cancel_lesson(self,cid,lid,reason=""):
        course=self.find_course_by_id(cid)
        if not course: return
        lesson=next((L for L in course.lessons if L.get("lesson_id")==lid), None)
        if not lesson: return
        lesson["cancelled"]=True
        self.lesson_changes.append({"action":"cancel","course_id":cid,"lesson_id":lid,"reason":reason,"timestamp":datetime.datetime.now().isoformat()})
        self._save_data()
        print(f"Lesson {lid} for {course.name} cancelled.")

    # checks for conflicts (room/teacher), updates lesson time/room, and logs the change
    def reschedule_lesson(self,cid,lid,new_day,new_time,new_room):
        course=self.find_course_by_id(cid)
        if not course: return
        lesson=next((L for L in course.lessons if L.get("lesson_id")==lid),None)

        if not lesson:
            print("Lesson not found.")
            return

        for c in self.courses:
            for L in c.lessons:
                if L["cancelled"]:
                    continue
                if self._same_slot(L["day"], L["start_time"], new_day, new_time):
                    if L["room"] == new_room:
                        print(f"Conflict: Room {new_room} already booked at that time.")
                        return
                    if c.teacher_id == course.teacher_id:
                        print(f"Conflict: Teacher has another lesson at that time.")
                        return

        lesson["day"] = new_day
        lesson["start_time"] = new_time
        lesson["room"] = new_room
        self.lesson_changes.append({
            "action":"reschedule",
            "course_id":cid,
            "lesson_id":lid,
            "new_day":new_day,
            "new_time":new_time,
            "new_room":new_room,
            "timestamp":datetime.datetime.now().isoformat()
        })
        self._save_data()
        print(f"Lesson {lid} for {course.name} rescheduled to {new_day} {new_time} in {new_room}.")

def front_desk_daily_roster(manager: ScheduleManager, day: str):
    """Displays a daily roster of all lessons on a given day."""
    day = day.strip().lower()
    print(f"\n--- Daily Roster for {day.capitalize()} ---")
    print(f"{'Course ID':<10} {'Course Name':<25} {'Teacher':<20} {'Time':<10} {'Room':<10} {'Cancelled':<10}")
    print("-" * 85)

    found = False
    for course in manager.courses:
        teacher = manager.find_teacher_by_id(course.teacher_id)
        for lesson in course.lessons:
            if lesson.get("day", "").strip().lower() == day:
                found = True
                print(f"{course.id:<10} {course.name:<25} "
                      f"{teacher.name if teacher else 'Unknown':<20} "
                      f"{lesson.get('start_time','TBD'):<10} "
                      f"{lesson.get('room','TBD'):<10} "
                      f"{'Yes' if lesson.get('cancelled') else 'No':<10}")
    if not found:
        print("No lessons scheduled for this day.")


# get integer from user and return None if user input "q"
def input_int(prompt, valid_ids=None):
    while True:
        hi = input(prompt).strip()
        if hi.lower() == 'q':
            return None
        if not hi.isdigit():
            print("Enter a valid number.")
            continue
        val_int = int(hi)
        if valid_ids is not None and val_int not in valid_ids:
            print("ID not found. Please enter a valid one.")
            continue
        return val_int

# allows student to check-in, submit feedback, view courses and grades
def student_menu(m: ScheduleManager):
    while True:
        print("\n--- Student Menu ---")
        print("1. Check-in")
        print("2. Submit Feedback")
        print("3. View Enrolled Courses")
        print("4. View Grades")
        print("Q. Back")
        choice = input("Choice: ").strip().lower()
        if choice == 'q':
            break

        student_id = input_int("Student ID: ", [s.id for s in m.students])
        if student_id is None: continue
        student = m.find_student_by_id(student_id)

        if choice == '1':
            if not student.enrolled_course_ids:
                print("No enrolled courses.")
                continue
            cid = input_int(f"Course ID: ", student.enrolled_course_ids)
            if cid: m.check_in(student_id, cid)
        elif choice == '2':
            if not student.enrolled_course_ids:
                print("No enrolled courses.")
                continue
            cid = input_int(f"Course ID to submit feedback: ", student.enrolled_course_ids)
            if cid:
                comment = input("Comment: ").strip()
                m.submit_feedback(student_id, cid, comment)
        elif choice == '3':
            print("Your courses:")
            for cid in student.enrolled_course_ids:
                c = m.find_course_by_id(cid)
                if c: print(f"{c.id}: {c.name} ({c.instrument})")
        elif choice == '4':
            print("Your grades:")
            for g in m.grades:
                if g.get("student_id")==student_id:
                    c = m.find_course_by_id(g.get("course_id"))
                    print(f"{c.name if c else g.get('course_id')}: {g.get('grade')} | Note: {g.get('note','')}")

# allows teacher to view courses, attendance, feedback, grades, and assign grades
def teacher_menu(m: ScheduleManager):
    while True:
        print("\n--- Teacher Menu ---")
        print("1. View Courses")
        print("2. View Attendance")
        print("3. View Feedbacks")
        print("4. View Grades")
        print("5. Assign Grades to Student")
        print("Q. Back")
        choice = input("Choice: ").strip().lower()
        if choice == 'q': 
            break   

        teacher_id = input_int("Your Teacher ID: ", [t.id for t in m.teachers])
        if teacher_id is None: continue
        teacher = m.find_teacher_by_id(teacher_id)

        if choice == '1':
            print("Your courses:")
            for c in m.courses:
                if c.teacher_id==teacher_id:
                    print(f"{c.id}: {c.name} ({c.instrument})")
        elif choice == '2':
            print("Attendance log:")
            for a in m.attendance_log:
                c = m.find_course_by_id(a.get("course_id"))
                if c and c.teacher_id==teacher_id:
                    s = m.find_student_by_id(a.get("student_id"))
                    print(f"{s.name if s else a.get('student_id')} - {c.name} at {a.get('timestamp')}")
        elif choice == '3':
            print("Feedbacks:")
            for f in m.feedbacks:
                c = m.find_course_by_id(f.get("course_id"))
                if c and c.teacher_id==teacher_id:
                    s = m.find_student_by_id(f.get("student_id"))
                    print(f"{s.name if s else f.get('student_id')} - {c.name}: {f.get('comment')}")
        elif choice == '4':
            print("Grades:")
            for g in m.grades:
                c = m.find_course_by_id(g.get("course_id"))
                if c and c.teacher_id==teacher_id:
                    s = m.find_student_by_id(g.get("student_id"))
                    print(f"{s.name if s else g.get('student_id')} - {c.name}: {g.get('grade')} | Note: {g.get('note','')}")
        elif choice == "5":
            tid = input_int("Your Teacher ID: ")
            sid = input_int("Student ID: ")
            cid = input_int("Course ID: ")
            grade = input("Grade (e.g., A, B, C): ")
            note = input("Note (optional): ")
            if None in (tid,sid,cid):
                continue
            m.assign_grade(tid, sid, cid, grade, note)

# allows schedule manager to switch courses, cancel/reschedule lessons
def schedule_manager_menu(m: ScheduleManager):
    while True:
        print("\n--- Schedule Manager Menu ---")
        print("1. Switch Course")
        print("2. Cancel Lesson")
        print("3. Reschedule Lesson")
        print("4. Daily Roster by Day")
        print("Q. Back")
        choice=input("Choice: ").strip().lower()
        if choice == 'q': 
            break

        if choice == '1':
            sid = input_int("Student ID: ", [s.id for s in m.students])
            from_cid = input_int("From Course ID: ", [c.id for c in m.courses])
            to_cid = input_int("To Course ID: ", [c.id for c in m.courses])
            if sid and from_cid and to_cid: m.switch_course(sid, from_cid, to_cid)
        elif choice == '2':
            cid=input_int("Course ID: ", [c.id for c in m.courses])
            if cid:
                lid = input_int("Lesson ID: ")
                if lid:
                    reason=input("Reason: ")
                    m.cancel_lesson(cid,lid,reason)
        elif choice == '3':
            cid = input_int("Course ID: ", [c.id for c in m.courses])
            if cid:
                lid = input_int("Lesson ID: ")
                if lid:
                    new_day = input("New day: ")
                    new_time = input("New time (HH:MM): ")
                    new_room = input("New room: ")
                    m.reschedule_lesson(cid,lid,new_day,new_time,new_room)
        elif choice == '4':
            day = input("Enter day (e.g., Monday): ")
            front_desk_daily_roster(m, day)

# allows receptionist to enroll students, record payments, set fees, and view reports
def receptionist_menu(m: ScheduleManager):
    while True:
        print("\n--- Receptionist Menu ---")
        print("1. Set Course Fee")
        print("2. Record Payment")
        print("3. Enroll Student")
        print("4. Atendance Report")
        print("5. Finance Report")
        print("6. List Students/Teachers/Courses")
        print("Q. Back")
        choice = input("Choice: ").strip().lower()
        if choice == 'q': 
            break

        if choice == '1':
            cid = input_int("Course ID: ", [c.id for c in m.courses])
            if cid:
                fee = input("New fee: ").strip()
                if fee.replace('.','',1).isdigit(): m.set_course_fee(cid,float(fee))
        elif choice == '2':
            sid = input_int("Student ID: ", [s.id for s in m.students])
            if sid:
                amt = input("Payment amount: ").strip()
                if amt.replace('.','',1).isdigit():
                    note = input("Note (optional): ")
                    m.record_payment(sid,float(amt),note)
        elif choice == "3":
            sid = input_int("Student ID: ", [s.id for s in m.students])
            cid = input_int("Course ID: ", [c.id for c in m.courses])
            if sid and cid: m.enroll_student(sid, cid)
        elif choice == "4":
            m.attendance_report()
        elif choice == "5":
            m.finance_report()
        elif choice == "6":
            print("\n--- Students ---")
            m.list_students()
            print("\n--- Teachers ---")
            m.list_teachers()
            print("\n--- Courses ---")
            m.list_courses()

# entry point of the program and loads data, shows role selection menu, and delegates to corresponding menus
def main():
    m = ScheduleManager()
    while True:
        print("\n--- MSMS v3 (Object-Oriented) ---")
        print("1. Student")
        print("2. Receptionist")
        print("3. Teacher")
        print("4. Scheduled Manager")
        print("Q. Quit")
        choice = input("Select role: ").strip().lower()
        while choice == "" :
            choice = input("Please select your role: ").strip().lower()
        if choice == 'q': break
        elif choice == '1': 
            student_menu(m)
        elif choice == '2': 
            receptionist_menu(m)
        elif choice == '3': 
            teacher_menu(m)
        elif choice == '4': 
            schedule_manager_menu(m)
        else:
            choice = input("Please select valid role: ").strip().lower()
            continue
        

if __name__ == "__main__":
    main()

