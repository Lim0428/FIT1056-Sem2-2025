# pst2_main.py - The Persistent Application

import json
import datetime
import random

DATA_FILE = "msms.json"
app_data = {} # This global dictionary will hold ALL our data.

# --- Core Persistence Engine ---
def load_data(path=DATA_FILE):
    """Loads all application data from a JSON file."""
    global app_data
    try:
        with open(path, 'r') as f:
            # TODO: Use json.load(f) to load the file's content into the global 'app_data' variable.
            app_data = json.load(f)
            print("Data loaded successfully.")
    except FileNotFoundError:
        print("Data file not found. Initializing with default structure.")
        # TODO: If the file doesn't exist, initialize 'app_data' with a default dictionary.
        # It should have keys like: "students", "teachers", "attendance", "next_student_id", "next_teacher_id".
        # The lists should be empty and the IDs should start at 1.
        app_data = {}

    default = {
            "students": [],
            "teachers": [],
            "attendance": [],
            "next_student_id": 1,
            "next_teacher_id": 1
    }
    for key, value in default.items():
        if key not in app_data:
            app_data[key] = value

def save_data(path=DATA_FILE):
    """Saves all application data to a JSON file."""
    # TODO: Open the file at 'path' in write mode ('w').
    # Use json.dump() to write the global 'app_data' dictionary to the file.
    # Use the 'indent=4' argument in json.dump() to make the file readable.
    with open(path, 'w') as f:
        json.dump(app_data, f, indent=4)
    print("Data saved successfully.")







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

# --- Main Application Loop ---
def st():
    while True:
        print("\n===== MSMS v2 (Persistent) =====")
        print("1.Student")
        print("2.Teacher")
        print("3.Quit")
        print("4.Print amount of student and teacher ")
        choice = input("Enter your character: ")

        if choice == "1":
            student()
        elif choice == "2":
            teacher()
        elif choice == "3":
            print("Quit the program......")
            break
        elif choice == "4":
            quick_stats()


def student():
    print("---Student Menu---")
    print("1.Check-in")
    print("2.Print Student Card")
    print("3.Update Student Info")
    print("4.Remove Student")
    print("5.Add Student")
    print("6.See Student Info")
    print("7.Random Student Selector")
    print("8.Back to Menu")
    
    choice = input("Enter yout choice: ")

    def getint(prompt):
        while True:
            value = input(prompt).strip()
            if value.isdigit():
                return int(value)
            print("Error: Please enter valid integer.")

    made_change = False # A flag to track if we need to save
    if choice == '1':
        student_id = getint("Enter your student ID: ")
        if student_id is None:
            return
        course_id = input("Enter your course ID: ").strip()
        while not course_id:
            print("Error: Do not enter blank.")
            course_id = input("Enter your course ID: ").strip()
        check_in(student_id,course_id)
        made_change = True

    elif choice == '2':
        student_id = getint("Enter student ID: ")
        if student_id is None:
            return
        print_student_card(student_id)

    elif choice == '3':
        student_id = getint("Enter your student ID: ")
        if student_id is None:
            return
        name = input("Enter new name: ")
        if name:
            for list in app_data["students"]:
                if list["id"]!= student_id:
                    continue
                list["name"]=name
                print("Student updated")
                made_change = True

    elif choice == '4':
        student_id = getint("Enter student ID to remove: ")
        remove_student(student_id)
        made_change = True

    elif choice == "5":
        name = input("Enter name: ").strip()
        while not name:
            print("Error: Name connot be empty.")
            name = input("Enter name: ").strip()
                
        courses_input = input("Enter courses: ").strip()
        while not courses_input:
            print("Error: Courses connot be empty.")
            courses_input = input("Enter courses: ").strip()

        enrolled_in = [d.strip() for d in courses_input.split(",") if d.strip()]
        add_student(name,enrolled_in)
        made_change = True
    elif choice == "6":
        see_student_info()
    elif choice == '7':
        random_student()
    elif choice == '8':
        return
    else:
        print("Invalid choice.")
            
    if made_change:
        save_data()

def teacher():
    print("---Teacher Menu---")
    print("1.Add teacher")
    print("2.Update Teacher Info")
    print("3.Remove Teacher")
    print("4.Back to Menu")
    choice = input("Enter your choice: ")

    def getint(prompt):
        while True:
            value = input(prompt).strip()
            if value.isdigit():
                return int(value)
            print("Error: Please enter valid integer.")

    made_change = False
    if choice == "1":
        name = input("Enter teacher name: ").strip()
        while not name:
            print("Error: Name cannot be blank.")
            name = input("Enter teacher name: ").strip()
        speciality = input("Enter speciality: ").strip()
        while not speciality:
            print("Error: Speciality cannot be blank.")
            speciality = input("Enter speciality: ").strip()

        add_teacher(name,speciality)
        made_change = True

    elif choice == "2":
        teacher_id = getint("Enter teacher ID: ")
        speciality = input("Enter new speciality: ").strip()
        while not speciality:
            print("Error: Speciality cannot be empty.")
            speciality = input("Enter new speciality: ").strip()
        update_teacher(teacher_id,speciality=speciality)
        made_change = True

    elif choice == "3":
        teacher_id = getint("Enter teacher ID: ")
        remove_teacher(teacher_id)
        made_change = True

    elif choice == "4":
        return
    else:
        print("Invalid choice.")

    if made_change:
        save_data()

def main():
    """Main function to run the MSMS application."""
    load_data() # Load all data from file at startup.
    quick_stats()
    
    st()

    save_data() # One final save on exit.

# --- Program Start ---
if __name__ == "__main__":
    main()