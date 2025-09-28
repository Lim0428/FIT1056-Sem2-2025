import json, datetime, os
# import json used to read/write JSON files for persistent storage
# import datetime used for timestamps (e.g., attendance, grades, payments)
# import os used to check if the JSON data file exist

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


# find stutend/ teacher and course by id
def find_student_by_id(self,sid):
    return next((s for s in self.students if s.id==sid), None)
def find_teacher_by_id(self,tid):
    return next((t for t in self.teachers if t.id==tid), None)
def find_course_by_id(self,cid):
    return next((c for c in self.courses if c.id==cid), None)