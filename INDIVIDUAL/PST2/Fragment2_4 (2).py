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