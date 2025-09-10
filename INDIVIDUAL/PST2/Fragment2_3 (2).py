
# --- New Receptionist Features ---
def check_in(student_id, course_id, timestamp=None):
    """Records a student's attendance for a course."""
    if timestamp is None:
        # TODO: Get the current time as a string using datetime.datetime.now().isoformat()
        timestamp = datetime.datetime.now().isoformat()
    
    # TODO: Create a check-in record dictionary.
    # It should contain 'student_id', 'course_id', and 'timestamp'.
    check_in_record = {
        "student_id": student_id,
        "course_id": course_id,
        "timestamp": timestamp
    }
    # TODO: Append this new record to the app_data['attendance'] list.
    app_data['attendance'].append(check_in_record)
    print(f"Receptionist: Student {student_id} checked into {course_id}.")

def quick_stats():
    print(f"Total Students: {len(app_data["students"])}")
    print(f"Total Teachers: {len(app_data["teachers"])}")


def print_student_card(student_id):
    """Creates a text file badge for a student."""
    # TODO: Find the student dictionary in app_data['students'].
    student_to_print = None
    for s in app_data['students']:
        if s['id'] == student_id:
            student_to_print = s
            break
    
    if student_to_print:
        # TODO: Create a filename, e.g., f"{student_id}_card.txt".
        filename = f"{student_id}_card.txt"
        # TODO: Open the file in write mode ('w').
        with open(filename, 'w') as f:
            # Write the student's details to the file in a nice format.
            f.write("========================\n")
            f.write(f"  MUSIC SCHOOL ID BADGE\n")
            f.write("========================\n")
            f.write(f"ID: {student_to_print['id']}\n")
            f.write(f"Name: {student_to_print['name']}\n")
            f.write(f"Enrolled In: {', '.join(student_to_print.get('enrolled_in', []))}\n")
        print(f"Printed student card to {filename}.")

        with open(filename, "r") as f:
            print(f.read())
    else:
        print(f"Error: Could not print card, student {student_id} not found.")

def see_student_info():
    s_id_input = input("Enter student ID to see: ")
    
    while not s_id_input.isdigit():
        print("Error: Student ID must be a integer.")
        s_id_input = input("Enter student ID to see: ")
    
    student_id = int(s_id_input)

    for student in app_data["students"]:
        if student["id"] == student_id:
            print(f"Student {student['name']} with student ID: {student['id']} have enrolled in:{','.join(student['enrolled_in']) if student['enrolled_in'] else "None"} ")
            return
    print(f"Error: Student with ID {student_id} not found.")

def random_student():
    if not app_data["students"]:
        print("No students available to select.")
        return
    
    student = random.choice(app_data["students"])
    print("#### Random Student Selected ####")
    print(f"ID: {student["id"]}")
    print(f"Name: {student['name']}")