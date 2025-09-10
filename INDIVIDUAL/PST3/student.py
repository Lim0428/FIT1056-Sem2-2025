from user import User

# inherit from user class to add enroll course, balance and payment
class StudentUser(User):
    def __init__(self, user_id, name):
        super().__init__(user_id, name)
        self.enrolled_course_ids = []   #list of enroll course ID
        self.balance = 0.0   #outstanding balance
        self.payments = []   #list of payment