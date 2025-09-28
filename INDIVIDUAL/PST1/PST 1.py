# MSMS.py - The In-Memory Prototype

# --- Data Models ---
class Student:
    """A blueprint for student objects. Holds their info."""
    def __init__(self, student_id, name):
        self.id = student_id
        self.name = name
        # TODO: Initialize an empty list called 'enrolled_in' to store instrument names.
        self.enrolled_in = []

class Teacher:
    """A blueprint for teacher objects."""
    def __init__(self, teacher_id, name, speciality):
        # TODO: Assign all three parameters (teacher_id, name, speciality)
        # to instance variables (e.g., self.id = teacher_id).
        self.id = teacher_id
        self.name = name
        self.speciality = speciality

# --- In-Memory Databases ---
# TODO: Create the global data stores.
student_db = []
teacher_db = []
next_student_id = 1
next_teacher_id = 1



# --- Core Helper Functions ---
def add_teacher(name, speciality):
    """Creates a Teacher object and adds it to the database."""
    global next_teacher_id
    # TODO: Create a new Teacher object using the next available ID.
    new_teacher = Teacher(next_teacher_id, name, speciality)
    # TODO: Append the new_teacher to the teacher_db list.
    teacher_db.append(new_teacher)
    # TODO: Increment the next_teacher_id counter.
    next_teacher_id += 1
    print(f"Core: Teacher '{name}' with speciality {speciality} added successfully.")


def list_students():
    """Prints all students in the database."""
    print("\n--- Student List ---")
    if not student_db:
        print("No students in the system.")
        return
    # TODO: Loop through student_db. For each student, print their ID, name, and their enrolled_in list.
    for student in student_db:
        print(f"  ID: {student.id}, Name: {student.name}, Enrolled in: {student.enrolled_in}")

def list_teachers():
    """Prints all teachers in the database."""
    # TODO: Implement the logic to list all teachers, similar to list_students().
    print("\n--- Teacher List ---")
    if not teacher_db:
        print("No teachers in the system.")
        return
    for teacher in teacher_db:
        print(f"  ID: {teacher.id}, Name: {teacher.name}, Speciality: {teacher.speciality}")

def find_students(term):
    """Finds students by name."""
    print(f"\n--- Finding Students matching '{term}' ---")
    # TODO: Create an empty list to store results.
    results = []
    # Loop through student_db. If the search 'term' (case-insensitive) is in the student's name,
    # add them to your results list.
    for student in student_db:
        name_match = term.lower() in student.name.lower()
        instrument_match = any(term.lower() in instrument.lower() for instrument in student.enrolled_in)
        if name_match or instrument_match:
            results.append(student)
    # After the loop, if the results list is empty, print "No match found."
    if not results:
        print("No match found.")
    # Otherwise, print the details for each student in the results list.
    else:
        for student in results:
            print(f"ID: {student.id}, Name: {student.name}, Enrolled in: {student.enrolled_in}")


def find_teachers(term):
    """Finds teachers by name or speciality."""
    # TODO: Implement this function similar to find_students, but check
    # for the term in BOTH the teacher's name AND their speciality.
    print(f"\n--- Finding Students matching '{term}' ---")
    results = []
    for teacher in teacher_db:
        if term.lower() in teacher.name.lower() or term.lower() in teacher.speciality.lower():
            results.append(teacher)
    if not results:
        print("No match found.")
    else:
        for teacher in results:
            print(f"ID: {teacher.id}, Name: {teacher.name}, Speciality: {teacher.speciality}")



# --- Front Desk Functions ---
def find_student_by_id(student_id):
    """A new helper to find one student by their exact ID."""
    # TODO: Loop through student_db. If a student's ID matches student_id, return the student object.
    for student in student_db:
        if student.id == student_id:
            return student
    # TODO: If the loop finishes without finding a match, return None.
    return None

def front_desk_register(name, instrument):
    """High-level function to register a new student and enrol them."""
    global next_student_id
    # TODO: Create a new Student object, add it to student_db, and increment the ID.
    new_student = Student(next_student_id, name)
    student_db.append(new_student)
    next_student_id += 1
    
    # TODO: Immediately call front_desk_enrol() using the new student's ID and the provided instrument.
    front_desk_enrol(new_student.id, instrument)
    print(f"Front Desk: Successfully registered '{name}' and enrolled them in '{instrument}'.")

def front_desk_enrol(student_id, instrument):
    """High-level function to enrol an existing student in a course."""
    instrument = instrument.replace(" ","")
    # TODO: Use your new find_student_by_id() helper.
    student = find_student_by_id(student_id)
    # TODO: If the student is found, append the instrument to their 'enrolled_in' list.
    if student:
        if instrument.lower() in [i.lower() for i in student.enrolled_in]:
            print(f" Error: Student {student_id} are not allowed to join the same instrument.")
        else:
            student.enrolled_in.append(instrument)
            print(f"Front Desk: Enrolled student {student_id}(student id) in '{instrument}'.")
    else:
        # TODO: If the student is not found, print an error message like "Error: Student ID not found."
        print(f"Error: Student ID {student_id} not found.")

def front_desk_lookup(term):
    """High-level function to search everything."""
    print(f"\n--- Performing lookup for '{term}' ---")
    find_students(term)
    find_teachers(term)



# --- Main Application ---
def main():
    """Runs the main interactive menu for the receptionist."""
    # Pre-populate some data for easy testing
    add_teacher("Dr. Keys", "Piano")
    add_teacher("Ms. Fret", "Guitar")

    while True:
        print("\n===== Music School Front Desk =====")
        print("1. Register New Student")
        print("2. Enrol Existing Student")
        print("3. Register New Teacher")
        print("4. Lookup Student or Teacher")
        print("5. (Admin) List all Students")
        print("6. (Admin) List all Teachers")
        print("q. Quit")
        
        choice = input("Enter your choice: ")

        if choice == '1':
            # TODO: Prompt for student name and instrument, then call front_desk_register.
            while True:
                name = input("Enter student name (‘x' to exit): ").strip()
                if name.lower() == "x":
                    break
                if name == "":
                    print("Name cannot be empty ~")
                    continue
        
                instrument = input("Enter instrument to enrol in ('x' to exit): ").replace(" ","").strip()
                if instrument.lower() == "x":
                    break
                if instrument == "":
                    print("Instrument cannot be empty ~")
                    continue

                front_desk_register(name, instrument)
                break
        elif choice == '2':
            # TODO: Prompt for student ID (as an int) and instrument, then call front_desk_enrol.
            while True:
                id = input("Enter student ID ('x' to exit): ").strip()

                if id.lower() == "x":
                    break
                if not id.isdigit():
                    print("Invalid ID. Please enter a number.")
                    continue

                instrument = input("Enter instrument to enrol in ('x' to exit): ")
                if instrument.lower() == "x":
                    break
                if instrument == "":
                    print("Instrument cannot be blank ~")
                    continue

                student_id = int(id)
                
                front_desk_enrol(student_id, instrument)
                break
            
        elif choice == "3":
            while True:
                name = input("Enter teacher name ('x' to exit):").strip()
                if name.lower() == "x":
                        break
                if not name:
                    print("Name cannot be blank ~")
                    continue

                speciality = input("Enter teacher speciality ('x' to exit):").replace(" ","").strip()
                if speciality.lower() == "x":
                    break
                if not speciality:
                    print("Speciality cannot be blank ~")
                    continue

                add_teacher(name, speciality)
                break
        elif choice == '4':
            # TODO: Prompt for a search term, then call front_desk_lookup.
            term = input("Enter search term: ")
            front_desk_lookup(term)
        elif choice == '5':
            list_students()
        elif choice == '6':
            list_teachers()
        elif choice.lower() == 'q':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


# --- Program Start ---
if __name__ == "__main__":
    main()