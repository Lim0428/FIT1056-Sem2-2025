    # --- Full CRUD for Core Data ---
# Note: We are now working with lists of dictionaries, not lists of objects.
def take_next_student_id():
    existing_ids = [list["id"] for list in app_data["students"]]
    new_id = 1
    while new_id in existing_ids:
        new_id += 1
    return new_id

def add_teacher(name, speciality):
    """Adds a teacher dictionary to the data store."""
    # TODO: Get the next teacher ID from app_data['next_teacher_id']
    # TODO: Create a new teacher dictionary with 'id', 'name', and 'speciality' keys.
    # TODO: Append the new dictionary to the app_data['teachers'] list.
    # TODO: Increment the 'next_teacher_id' in app_data.
    teacher_id = app_data['next_teacher_id']
    new_teacher = {"id": teacher_id, "name": name, "speciality": speciality}
    app_data['teachers'].append(new_teacher)
    app_data['next_teacher_id'] += 1
    print(f"Core: Teacher '{name}' added.")

def add_student(name,enrolled_in=None):
    if enrolled_in is None:
        enrolled_in = []
    exist_ids = {student["id"] for student in app_data["students"]}
    new_id = 1
    while new_id in exist_ids:
        new_id += 1
    new_student = {"id": new_id, "name":name, "enrolled_in": enrolled_in}
    app_data["students"].append(new_student)
    print(f"Students '{name}' added with ID: {new_id}")

def update_teacher(teacher_id, **fields):
    """Finds a teacher by ID and updates their data with provided fields."""
    # TODO: Loop through the app_data['teachers'] list.
    for teacher in app_data['teachers']:
        # TODO: If a teacher's 'id' matches teacher_id:
        if teacher['id'] == teacher_id:
            # Use the .update() method on the teacher dictionary to apply the 'fields'.
            teacher.update(fields)
            print(f"Teacher {teacher_id} updated.")
            return
    print(f"Error: Teacher with ID {teacher_id} not found.")

def update_student(student_id, **fields):
    for student in app_data["students"]:
        if student["id"] == student_id:
            student.update(fields)
            print(f"Student {student_id} updated.")
            return
    print(f"Error: Student with ID {student_id} not found.")

def remove_student(student_id):
    """Removes a student from the data store."""
    app_data['students'] = [s for s in app_data["students"] if s['id'] != student_id]
    print(f"Student {student_id} removed.")
# TODO: Implement remove_teacher() and update_student() using the patterns above.

def remove_teacher(teacher_id):
    app_data["teachers"] = [t for t in app_data["teachers"] if t["id"] != teacher_id]
    print(f"Teacher {teacher_id} removed.")

