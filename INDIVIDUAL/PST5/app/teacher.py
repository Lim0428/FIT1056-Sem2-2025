from app.user import User

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

        