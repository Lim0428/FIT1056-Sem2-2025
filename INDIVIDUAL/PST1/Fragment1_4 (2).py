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