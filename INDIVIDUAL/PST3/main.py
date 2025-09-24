# main.py - The View Layer
import streamlit as st
from schedule import ScheduleManager 

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


def main():
    m = ScheduleManager(data_path="C:/Users/user/OneDrive/Documents/FIT1056-github/INDIVIDUAL/PST3/msms.json")
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