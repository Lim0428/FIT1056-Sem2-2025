import json
from student import StudentUser
from teacher import TeacherUser, Course

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