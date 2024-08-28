import mysql.connector
import re # For regular expressions to validate input
import os
from tabulate import tabulate
import getpass
from datetime import datetime
import hashlib  # For password hashing (you may want to use bcrypt for better security)


# Establishing a connection to MySQL
try:
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Devu@22112002',  # Replace with your actual MySQL root password
        database='project'  # Using 'project' database
    )
    cursor = db.cursor()
except mysql.connector.Error as err:
    print(f"Error: {err}")
    exit()


def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80  # Default width if unable to get terminal size


def print_centered(text, width=None):
    if width is None:
        width = get_terminal_width()
    print(text.center(width))


def print_header(title, underline_char='='):
    width = get_terminal_width()
    underline = underline_char * width
    print(underline)
    print_centered(title)
    print(underline)
    print()


def prompt_input(prompt, allow_back=False):
    while True:
        user_input = input(prompt).strip()
        if user_input == '0' and allow_back:
            return None  # Indicates to go back
        elif user_input:
            return user_input
        else:
            print("Input cannot be empty. Please try again.")


# User authentication and registration

# Function to hash passwords (you can replace it with bcrypt or another secure method)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Function to validate email format
def validate_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email)


# Function to validate first name and last name
def validate_name(name):
    return name.isalpha()


# Function to validate password strength
def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d.*\d", password):  # At least two digits
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):  # At least one special character
        return False
    return True


def register():
    print_header("Register New User")

    # Validate first name
    while True:
        first_name = prompt_input("Enter First Name: ")
        if not validate_name(first_name):
            print("First Name must contain only alphabetic characters.")
        else:
            break

    # Validate last name
    while True:
        last_name = prompt_input("Enter Last Name: ")
        if not validate_name(last_name):
            print("Last Name must contain only alphabetic characters.")
        else:
            break

    # Validate email
    while True:
        email = prompt_input("Enter Email: ")
        if not validate_email(email):
            print("Invalid email format. Please enter a valid email with '@' and a valid domain.")
        else:
            # Check if email already exists
            cursor.execute("SELECT email FROM users WHERE email = %s UNION SELECT email FROM admins WHERE email = %s",
                           (email, email))
            if cursor.fetchone():
                print("Email already exists. Try logging in.")
                return
            break

    # Validate password
    while True:
        password = prompt_input("Enter Password: ")
        if not validate_password(password):
            print(
                "Password must be at least 8 characters long, contain at least one special character, two digits, and a mix of uppercase and lowercase letters.")
        else:
            hashed_password = hash_password(password)  # Hash the password
            break

    username = prompt_input("Enter Username: ")
    role = prompt_input("Enter Role (user or admin): ").lower()

    if role == 'user':
        # Insert the user into the 'users' table
        cursor.execute("""
            INSERT INTO users (first_name, last_name, email, username, password)
            VALUES (%s, %s, %s, %s, %s)
        """, (first_name, last_name, email, username, hashed_password))
        db.commit()
        print("User registration successful! You can now log in.")

    elif role == 'admin':
        secret_code = prompt_input("Enter the secret code for admin registration: ")

        # Replace 'super_secret_code' with the actual secret code for admins
        if secret_code != "secret_code":
            print("Invalid secret code. You cannot register as an admin.")
            return

        # Insert the admin into the 'admins' table
        cursor.execute("""
            INSERT INTO admins (full_name, email, username, password, role)
            VALUES (%s, %s, %s, %s, 'admin')
        """, (f"{first_name} {last_name}", email, username, hashed_password))
        db.commit()
        print("Admin registration successful! You can now log in.")


    else:
        print("Invalid role. Please choose either 'user' or 'admin'.")


def login():
    print_header("Login")

    # Validate email
    while True:
        email = prompt_input("Enter Email: ")
        if not validate_email(email):
            print("Invalid email format. Please enter a valid email with '@' and a valid domain.")
        else:
            break

    password = prompt_input("Enter Password: ")
    hashed_password = hash_password(password)  # Hash the input password to match with stored hashed password

    # Check for the user in the 'users' table
    cursor.execute("SELECT user_id FROM users WHERE email = %s AND password = %s", (email, hashed_password))
    user = cursor.fetchone()

    if user:
        user_id = user[0]
        print(f"Login successful! Welcome, {email}")
        user_menu(user_id)  # Direct to user menu
    else:
        # If not found in users, check in the 'admins' table
        cursor.execute("SELECT admin_id, role FROM admins WHERE email = %s AND password = %s", (email, hashed_password))
        admin = cursor.fetchone()

        if admin:
            admin_id, role = admin
            print(f"Login successful! Welcome, {email}")
            admin_menu(admin_id)  # Direct to admin menu based on role
        else:
            print("Invalid email or password. Please try again.")


# User Management Functions for Admin
def list_membership_users():
    print_header("Membership Users")
    cursor.execute("""
        SELECT user_id, first_name, last_name, email, membership_plan_id 
        FROM users WHERE membership_plan_id IS NOT NULL
    """)
    users = cursor.fetchall()
    if users:
        print(tabulate(users, headers=["User ID", "First Name", "Last Name", "Email", "Plan ID"]))
    else:
        print("No membership users found.")
    input("\nPress Enter to go back...")


#=========================view_membership_plan_guest() --> only viewing the membership details to the guest users

def view_membership_plan_guest():
    print_header("View Membership Plans")
    cursor.execute("""
        SELECT plan_id, plan_name, plan_duration, plan_price, description, benefits, max_borrowings, borrowing_period, renewal_fee, late_fee
        FROM membership_plans
        WHERE is_active = TRUE
    """)
    plans = cursor.fetchall()
    if plans:
        print(tabulate(plans, headers=["Plan ID", "Plan Name", "Duration (days)", "Price (₹)", "Description", "Benefits", "Max Borrowings", "Borrowing Period (days)", "Renewal Fee (₹)", "Late Fee (₹)"]))
    else:
        print("No active membership plans available.")
    input("\nPress Enter to go back...")

def list_guest_users():
    print_header("Guest Users")
    cursor.execute("""
        SELECT user_id, first_name, last_name, email 
        FROM users WHERE membership_plan_id IS NULL
    """)
    guests = cursor.fetchall()
    if guests:
        print(tabulate(guests, headers=["User ID", "First Name", "Last Name", "Email"]))
    else:
        print("No guest users found.")
    input("\nPress Enter to go back...")

#=======================================list_all_members() --> listing all the members for admin dashboard
def list_all_members():
    print_header("List of All Users (Guests and Membership Users)")

    # Adjust the query based on the actual columns in your table
    cursor.execute("SELECT user_id, first_name, last_name, email FROM users ORDER BY user_id")
    users = cursor.fetchall()

    if not users:
        print("No users found.")
        return

    # Print the details of each user
    print(f"{'User ID':<10} {'First Name':<15} {'Last Name':<15} {'Email':<30}")
    print("-" * 70)

    for user in users:
        user_id, first_name, last_name, email = user
        print(f"{user_id:<10} {first_name:<15} {last_name:<15} {email:<30}")

    input("\nPress Enter to go back...")


def search_users():
    print_header("Search Users")
    search_query = prompt_input("Enter name or email to search: ")
    cursor.execute("""
        SELECT user_id, first_name, last_name, email FROM users 
        WHERE first_name LIKE %s OR last_name LIKE %s OR email LIKE %s
    """, ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
    results = cursor.fetchall()
    if results:
        print(tabulate(results, headers=["User ID", "First Name", "Last Name", "Email"]))
    else:
        print("No users found.")
    input("\nPress Enter to go back...")


def delete_user():
    print_header("Delete User")

    # Ask user to choose between removing by user_id or email
    choice = input("Would you like to delete the user by ID (1) or Email (2)? Enter 1 or 2: ").strip()

    if choice == '1':
        # Delete by user_id
        user_id = prompt_input("Enter the User ID to delete: ")
        cursor.execute("SELECT first_name, last_name, email FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print(f"User with ID '{user_id}' not found.")
            return
        confirm = input(
            f"Are you sure you want to delete the user '{user[0]} {user[1]}' (Email: {user[2]})? (y/n): ").strip().lower()
        if confirm == 'y':
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            db.commit()
            print("User deleted successfully!")
        else:
            print("Operation canceled.")

    elif choice == '2':
        # Delete by email
        email = prompt_input("Enter the User Email to delete: ")
        cursor.execute("SELECT user_id, first_name, last_name FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            print(f"User with email '{email}' not found.")
            return
        confirm = input(
            f"Are you sure you want to delete the user '{user[1]} {user[2]}' (User ID: {user[0]})? (y/n): ").strip().lower()
        if confirm == 'y':
            cursor.execute("DELETE FROM users WHERE email = %s", (email,))
            db.commit()
            print("User deleted successfully!")
        else:
            print("Operation canceled.")

    else:
        print("Invalid choice. Please select either 1 or 2.")

    input("\nPress Enter to go back...")


def update_user():
    print_header("Update User")

    # Prompt the admin to enter the User ID they want to update
    user_id = input("Enter the User ID to update: ").strip()

    # Fetch the current details of the user
    cursor.execute("SELECT first_name, last_name, email FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        print("User not found.")
        return

    # Display the current details to the admin
    current_first_name, current_last_name, current_email = user
    print(f"\nCurrent Details for User ID {user_id}:")
    print(f"First Name: {current_first_name}")
    print(f"Last Name: {current_last_name}")
    print(f"Email: {current_email}")

    # Prompt the admin to enter new details or press Enter to keep the current ones
    new_first_name = input("Enter new first name or press Enter to keep the current: ").strip()
    new_last_name = input("Enter new last name or press Enter to keep the current: ").strip()
    new_email = input("Enter new email or press Enter to keep the current: ").strip()

    # If no new input is given, keep the current details
    updated_first_name = new_first_name if new_first_name else current_first_name
    updated_last_name = new_last_name if new_last_name else current_last_name
    updated_email = new_email if new_email else current_email

    # Update the user's details in the database
    cursor.execute("""
        UPDATE users SET first_name = %s, last_name = %s, email = %s
        WHERE user_id = %s
    """, (updated_first_name, updated_last_name, updated_email, user_id))
    db.commit()

    print("\nUser updated successfully!")
    input("\nPress Enter to go back...")


#=============================== Book Management Functions for Admin===================================================

#list all books

def list_all_books():
    print_header("List of All Books")

    # Fetch all books with relevant details (title, author, genre, language, available copies)
    cursor.execute("""
        SELECT books.book_id, books.title, authors.author_name, genres.genre_name, 
               languages.language_name, books.available_copies
        FROM books
        JOIN authors ON books.author_id = authors.author_id
        JOIN genres ON books.genre_id = genres.genre_id
        JOIN languages ON books.language_id = languages.language_id
    """)

    books = cursor.fetchall()

    if not books:
        print("No books found.")
        return

    # Print the books in a formatted table
    print(f"{'Book ID':<10} {'Title':<30} {'Author':<20} {'Genre':<15} {'Language':<15} {'Available Copies':<15}")
    print("-" * 105)

    for book in books:
        print(f"{book[0]:<10} {book[1]:<30} {book[2]:<20} {book[3]:<15} {book[4]:<15} {book[5]:<15}")

    input("\nPress Enter to go back...")


#add a new book
def add_book():
    print_header("Add New Book", '-')
    title = prompt_input("Enter book title: ")
    author_name = prompt_input("Enter author name: ")
    cursor.execute("SELECT author_id FROM authors WHERE author_name = %s", (author_name,))
    author = cursor.fetchone()
    if not author:
        cursor.execute("INSERT INTO authors (author_name) VALUES (%s)", (author_name,))
        db.commit()
        author_id = cursor.lastrowid
    else:
        author_id = author[0]

    genre_name = prompt_input("Enter genre: ")
    cursor.execute("SELECT genre_id FROM genres WHERE genre_name = %s", (genre_name,))
    genre = cursor.fetchone()
    if not genre:
        cursor.execute("INSERT INTO genres (genre_name) VALUES (%s)", (genre_name,))
        db.commit()
        genre_id = cursor.lastrowid
    else:
        genre_id = genre[0]

    language_name = prompt_input("Enter language: ")
    cursor.execute("SELECT language_id FROM languages WHERE language_name = %s", (language_name,))
    language = cursor.fetchone()
    if not language:
        cursor.execute("INSERT INTO languages (language_name) VALUES (%s)", (language_name,))
        db.commit()
        language_id = cursor.lastrowid
    else:
        language_id = language[0]

    available_copies = prompt_input("Enter available copies: ")
    cursor.execute("""
        INSERT INTO books (title, author_id, genre_id, language_id, available_copies) 
        VALUES (%s, %s, %s, %s, %s)
    """, (title, author_id, genre_id, language_id, available_copies))
    db.commit()
    print("Book added successfully!")


def update_book():
    print_header("Update Book")
    book_id = prompt_input("Enter the Book ID to update: ")

    # Fetch the current book details
    cursor.execute("""
        SELECT books.book_id, books.title, authors.author_name, genres.genre_name, 
               languages.language_name, books.available_copies
        FROM books
        JOIN authors ON books.author_id = authors.author_id
        JOIN genres ON books.genre_id = genres.genre_id
        JOIN languages ON books.language_id = languages.language_id
        WHERE books.book_id = %s
    """, (book_id,))

    book = cursor.fetchone()

    if not book:
        print("Book not found.")
        return

    # Display current book details
    print(f"\nCurrent Book Details:\n"
          f"Title: {book[1]}\n"
          f"Author: {book[2]}\n"
          f"Genre: {book[3]}\n"
          f"Language: {book[4]}\n"
          f"Available Copies: {book[5]}\n")

    # Use input() directly and skip prompt_input() for optional fields
    # This will allow user to press Enter without interruption
    title = input("Enter new title or press Enter to keep current: ").strip()
    author_name = input("Enter new author name or press Enter to keep current: ").strip()
    genre_name = input("Enter new genre name or press Enter to keep current: ").strip()
    language_name = input("Enter new language name or press Enter to keep current: ").strip()
    available_copies = input("Enter new available copies or press Enter to keep current: ").strip()

    # Resolve foreign key values based on input names
    if author_name:
        cursor.execute("SELECT author_id FROM authors WHERE author_name = %s", (author_name,))
        author = cursor.fetchone()
        if author:
            author_id = author[0]
        else:
            print(f"Author '{author_name}' not found.")
            return
    else:
        # Using the original author_id
        cursor.execute("SELECT author_id FROM authors WHERE author_name = %s", (book[2],))
        author_id = cursor.fetchone()[0]

    if genre_name:
        cursor.execute("SELECT genre_id FROM genres WHERE genre_name = %s", (genre_name,))
        genre = cursor.fetchone()
        if genre:
            genre_id = genre[0]
        else:
            print(f"Genre '{genre_name}' not found.")
            return
    else:
        # Using the original genre_id
        cursor.execute("SELECT genre_id FROM genres WHERE genre_name = %s", (book[3],))
        genre_id = cursor.fetchone()[0]

    if language_name:
        cursor.execute("SELECT language_id FROM languages WHERE language_name = %s", (language_name,))
        language = cursor.fetchone()
        if language:
            language_id = language[0]
        else:
            print(f"Language '{language_name}' not found.")
            return
    else:
        # Using the original language_id
        cursor.execute("SELECT language_id FROM languages WHERE language_name = %s", (book[4],))
        language_id = cursor.fetchone()[0]

    # Update the book in the database, keeping original values where input was skipped
    cursor.execute("""
        UPDATE books 
        SET title = %s, author_id = %s, genre_id = %s, language_id = %s, available_copies = %s
        WHERE book_id = %s
    """, (title or book[1], author_id, genre_id, language_id, available_copies or book[5], book_id))

    db.commit()
    print("Book updated successfully!")
    input("\nPress Enter to go back...")


def remove_book():
    print_header("Remove Book")

    # Ask user to choose between removing by book_id or title
    choice = input("Would you like to remove the book by ID (1) or Title (2)? Enter 1 or 2: ").strip()

    if choice == '1':
        # Remove by book_id
        book_id = prompt_input("Enter the Book ID to delete: ")
        cursor.execute("SELECT title FROM books WHERE book_id = %s", (book_id,))
        book = cursor.fetchone()
        if not book:
            print(f"Book with ID '{book_id}' not found.")
            return
        confirm = input(f"Are you sure you want to delete the book titled '{book[0]}'? (y/n): ").strip().lower()
        if confirm == 'y':
            cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
            db.commit()
            print("Book removed successfully!")
        else:
            print("Operation canceled.")

    elif choice == '2':
        # Remove by title
        title = prompt_input("Enter the Book Title to delete: ")
        cursor.execute("SELECT book_id FROM books WHERE title = %s", (title,))
        book = cursor.fetchone()
        if not book:
            print(f"Book with title '{title}' not found.")
            return
        confirm = input(f"Are you sure you want to delete the book titled '{title}'? (y/n): ").strip().lower()
        if confirm == 'y':
            cursor.execute("DELETE FROM books WHERE title = %s", (title,))
            db.commit()
            print("Book removed successfully!")
        else:
            print("Operation canceled.")

    else:
        print("Invalid choice. Please select either 1 or 2.")

    input("\nPress Enter to go back...")


#list_all_borrowed_books() --> for admin to see all borrowed books by the users

from datetime import datetime

def list_all_borrowed_books():
    print_header("List of All Borrowed Books")

    # Fetch all borrowed books with relevant details (user_name, book_name, borrow_date, return_date)
    cursor.execute("""
        SELECT borrowed_books.borrow_id, CONCAT(users.first_name, ' ', users.last_name) AS user_name, 
               books.title AS book_name, borrowed_books.borrow_date, borrowed_books.return_date
        FROM borrowed_books
        JOIN users ON borrowed_books.user_id = users.user_id
        JOIN books ON borrowed_books.book_id = books.book_id
    """)

    borrowed_books = cursor.fetchall()

    if not borrowed_books:
        print("No borrowed books found.")
        return

    # Print the borrowed books in a formatted table
    print(f"{'Borrow ID':<10} {'User Name':<25} {'Book Name':<30} {'Borrow Date':<15} {'Return Date':<15}")
    print("-" * 95)

    # Loop through the borrowed books and format the dates
    for book in borrowed_books:
        borrow_date = book[3].strftime('%Y-%m-%d') if book[3] else 'N/A'
        return_date = book[4].strftime('%Y-%m-%d') if book[4] else 'N/A'

        print(f"{book[0]:<10} {book[1]:<25} {book[2]:<30} {borrow_date:<15} {return_date:<15}")

    input("\nPress Enter to go back...")



# Rental History Functionality for Admin
def view_rental_history():
    print_header("Rental History")
    cursor.execute("""
        SELECT borrowed_books.borrow_id, users.first_name, users.last_name, books.title, 
               borrowed_books.borrow_date, borrowed_books.return_date
        FROM borrowed_books
        JOIN users ON borrowed_books.user_id = users.user_id
        JOIN books ON borrowed_books.book_id = books.book_id
    """)
    history = cursor.fetchall()
    if history:
        print(tabulate(history,
                       headers=["Borrow ID", "First Name", "Last Name", "Book Title", "Borrow Date", "Return Date"]))
    else:
        print("No rental history found.")
    input("\nPress Enter to go back...")

#====================membership management functions for admin to perform CRUD operations========================

# Admin functions to add, update, and delete membership plans

# Function for admin to list all current membership plans
def list_all_membership_admin():
    print_header("Current Membership Plans")
    try:
        cursor.execute("""
            SELECT plan_id, plan_name, plan_duration, plan_price, renewal_fee, late_fee, description, benefits, is_active
            FROM membership_plans
        """)
        plans = cursor.fetchall()

        if plans:
            print(
                tabulate(plans, headers=["Plan ID", "Plan Name", "Duration (days)", "Price", "Renewal Fee", "Late Fee",
                                         "Description", "Benefits", "Active"]))
        else:
            print("No membership plans available.")
    except Exception as e:
        print(f"Error fetching membership plans: {e}")

    input("\nPress Enter to go back...")


def add_membership_plan():
    print_header("Add Membership Plan")

    plan_name = prompt_input("Enter plan name: ")

    while True:
        try:
            duration = int(prompt_input("Enter plan duration (days): "))
            break
        except ValueError:
            print("Invalid input. Please enter a number.")

    while True:
        try:
            price = float(prompt_input("Enter plan price: "))
            break
        except ValueError:
            print("Invalid input. Please enter a valid price.")

    while True:
        try:
            renewal_fee = float(prompt_input("Enter renewal fee: "))
            break
        except ValueError:
            print("Invalid input. Please enter a valid renewal fee.")

    while True:
        try:
            late_fee = float(prompt_input("Enter late fee: "))
            break
        except ValueError:
            print("Invalid input. Please enter a valid late fee.")

    description = prompt_input("Enter plan description: ")
    benefits = prompt_input("Enter plan benefits: ")

    try:
        cursor.execute("""
            INSERT INTO membership_plans (plan_name, plan_duration, plan_price, description, benefits, renewal_fee, late_fee, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        """, (plan_name, duration, price, description, benefits, renewal_fee, late_fee))
        db.commit()
        print("Membership plan added successfully.")
    except Exception as e:
        print(f"Error adding membership plan: {e}")


def delete_membership_plan():
    print_header("Delete Membership Plan")
    plan_id = input("Enter plan ID to delete (press Enter to search by name): ")

    if not plan_id:
        plan_name = prompt_input("Enter plan name to delete: ")
        cursor.execute("SELECT plan_id, plan_name FROM membership_plans WHERE plan_name = %s", (plan_name,))
        result = cursor.fetchone()
        if result:
            plan_id, plan_name = result
            confirm = prompt_input(f"Are you sure you want to delete the plan '{plan_name}' (ID: {plan_id})? (y/n): ")
            if confirm.lower() == 'y':
                try:
                    cursor.execute("DELETE FROM membership_plans WHERE plan_id = %s", (plan_id,))
                    db.commit()
                    print(f"Membership plan '{plan_name}' deleted successfully.")
                except Exception as e:
                    print(f"Error deleting membership plan: {e}")
            else:
                print("Deletion canceled.")
        else:
            print(f"Membership plan with name '{plan_name}' not found.")
    else:
        try:
            cursor.execute("DELETE FROM membership_plans WHERE plan_id = %s", (plan_id,))
            db.commit()
            print(f"Membership plan with ID {plan_id} deleted successfully.")
        except Exception as e:
            print(f"Error deleting membership plan: {e}")



def update_membership_plan():
    print_header("Update Membership Plan")

    # Provide an option to either search by ID or by name
    print("1. Search by Plan ID")
    print("2. Search by Plan Name")
    search_option = prompt_input("Choose an option (1/2): ")

    # Initialize plan_id variable
    plan_id = None

    if search_option == '1':
        # Search by Plan ID
        plan_id = prompt_input("Enter plan ID to update: ")
    elif search_option == '2':
        # Search by Plan Name
        plan_name = input("Enter plan name to update: ")
        cursor.execute("SELECT plan_id FROM membership_plans WHERE plan_name = %s", (plan_name,))
        result = cursor.fetchone()
        if result:
            plan_id = result[0]
        else:
            print(f"Membership plan with name '{plan_name}' not found.")
            return
    else:
        print("Invalid option. Please try again.")
        return

    # If plan ID is found, fetch the current details
    cursor.execute("""
        SELECT plan_name, plan_duration, plan_price, renewal_fee, late_fee, description, benefits
        FROM membership_plans WHERE plan_id = %s
    """, (plan_id,))
    current_plan = cursor.fetchone()

    if not current_plan:
        print(f"Membership plan with ID {plan_id} not found.")
        return

    print("Press Enter to keep current value:")

    new_plan_name = prompt_input(f"Plan Name [{current_plan[0]}]: ") or current_plan[0]

    while True:
        try:
            new_duration = input(f"Plan Duration (days) [{current_plan[1]}]: ")
            new_duration = int(new_duration) if new_duration else current_plan[1]
            break
        except ValueError:
            print("Invalid input. Please enter a number.")

    while True:
        try:
            new_price = input(f"Plan Price [{current_plan[2]}]: ")
            new_price = float(new_price) if new_price else current_plan[2]
            break
        except ValueError:
            print("Invalid input. Please enter a valid price.")

    while True:
        try:
            new_renewal_fee = input(f"Renewal Fee [{current_plan[3]}]: ")
            new_renewal_fee = float(new_renewal_fee) if new_renewal_fee else current_plan[3]
            break
        except ValueError:
            print("Invalid input. Please enter a valid renewal fee.")

    while True:
        try:
            new_late_fee = input(f"Late Fee [{current_plan[4]}]: ")
            new_late_fee = float(new_late_fee) if new_late_fee else current_plan[4]
            break
        except ValueError:
            print("Invalid input. Please enter a valid late fee.")

    new_description = input(f"Description [{current_plan[5]}]: ") or current_plan[5]
    new_benefits = input(f"Benefits [{current_plan[6]}]: ") or current_plan[6]

    try:
        cursor.execute("""
            UPDATE membership_plans
            SET plan_name = %s, plan_duration = %s, plan_price = %s, renewal_fee = %s, late_fee = %s, description = %s, benefits = %s
            WHERE plan_id = %s
        """, (new_plan_name, new_duration, new_price, new_renewal_fee, new_late_fee, new_description,
              new_benefits, plan_id))
        db.commit()
        print(f"Membership plan '{new_plan_name}' updated successfully.")
    except Exception as e:
        print(f"Error updating membership plan: {e}")

#===================================================supports for admin view reviews=====================================

def view_review_admin(book_id):
    print_header("View Reviews (Admin)")

    # Retrieve reviews for the book
    cursor.execute("""
        SELECT r.review_id, r.review_text, u.username
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.book_id = %s
    """, (book_id,))

    reviews = cursor.fetchall()
    if not reviews:
        print("No reviews found.")
        return

    # Display reviews
    print("\nReviews:")
    for i, review in enumerate(reviews):
        print(f"{i+1}. {review[1]} by {review[2]}")

    # Admin options
    while True:
        print("\nOptions:")
        print("1. Update review")
        print("2. Delete review")
        print("3. Back to main menu")
        choice = input("Enter your choice: ")

        if choice == "1":
            review_id = int(input("Enter the number of the review to update: ")) - 1
            review_text = input("Enter the updated review text: ")
            cursor.execute("""
                UPDATE reviews
                SET review_text = %s
                WHERE review_id = %s
            """, (review_text, reviews[review_id][0]))
            db.commit()
            print("Review updated successfully!")

        elif choice == "2":
            review_id = int(input("Enter the number of the review to delete: ")) - 1
            cursor.execute("""
                DELETE FROM reviews
                WHERE review_id = %s
            """, (reviews[review_id][0],))
            db.commit()
            print("Review deleted successfully!")

        elif choice == "3":
            break

        else:
            print("Invalid choice. Please try again.")


#====================================================== Menu for Admin =====================================
def admin_menu(admin_id):
    while True:
        print_header("Admin Dashboard")
        print("1. Manage Users")
        print("2. Manage Books")
        print("3. Manage Reviews")
        print("4. Manage Membership")
        # print("5. View Rental History")
        print("0. Logout")
        choice = prompt_input("Enter your choice: ")

        if choice == '1':
            while True:
                print_header("Manage Users")
                print("1. List All Users")
                print("2. List Membership Users")
                print("3. List Guest Users")
                print("4. Search Users")
                print("5. Update User")
                # print("6. Delete User")
                print("6. Back")
                user_choice = prompt_input("Enter your choice: ", allow_back=True)

                if user_choice == '1':
                    list_all_members()
                elif user_choice == '2':
                    list_membership_users()
                elif user_choice == '3':
                    list_guest_users()
                elif user_choice == '4':
                    search_users()
                elif user_choice == '5':
                    update_user()
                elif user_choice == '6':
                    break
                else:
                    print("Invalid choice. Please try again.")

        elif choice == '2':
            while True:
                print_header("Manage Books")
                print("1. List all books")
                print("2. Add Book")
                print("3. Update Book")
                print("4. Remove Book")
                print("5. List borrowed books")
                print("6. Back")
                book_choice = prompt_input("Enter your choice: ", allow_back=True)
                if book_choice == '1':
                    list_all_books()
                elif book_choice == '2':
                    add_book()
                elif book_choice == '3':
                    update_book()
                elif book_choice == '4':
                    remove_book()
                elif book_choice == '5':
                    list_all_borrowed_books()
                elif book_choice == '6':
                    break
                else:
                    print("Invalid choice. Please try again.")

        elif choice == '3':
            while True:
                print_header("Manage Reviews")
                print("1. View All Reviews")
                print("2. Delete Review")
                print("3. Edit Review")
                print("4. Search Reviews by Title")
                print("5. Back")
                admin_mgmt_choice = prompt_input("Enter your choice: ", allow_back=True)

                if admin_mgmt_choice == '1':
                    view_all_reviews()
                elif admin_mgmt_choice == '2':
                    delete_review()
                elif admin_mgmt_choice == '3':
                    edit_review()
                elif admin_mgmt_choice == '4':
                    title = input("Enter the book title to search reviews: ")
                    search_reviews_by_title(title)
                elif admin_mgmt_choice == '5':
                    break
                else:
                    print("Invalid choice. Please try again.")

        elif choice == '4':
            while True:
                print_header("Manage Membership Plans")
                print("1. Current Membership Plans")
                print("2. Add Membership Plan")
                print("3. Update Membership Plan")
                print("4. Delete Membership Plan")  # Adding Delete option
                print("5. Back")  # Adjusting the back option to 5
                membership_choice = prompt_input("Enter your choice: ", allow_back=True)

                if membership_choice == '1':
                    list_all_membership_admin()  # List all membership plans
                elif membership_choice == '2':
                    add_membership_plan()  # Add new membership plan
                elif membership_choice == '3':
                    update_membership_plan()  # Update existing membership plan
                elif membership_choice == '4':
                    delete_membership_plan()  # Delete membership plan
                elif membership_choice == '5':  # Adjusted to 5 as Back option
                    break
                else:
                    print("Invalid choice. Please try again.")

        elif choice == '0':
            break
#=============================================reviews management both admin and user===================================
# Function for users to add reviews
# def add_review(user_id):
#     print_header("Add a Review")
#
#     # Fetch the list of books borrowed by the user
#     cursor.execute("""
#         SELECT b.book_id, b.title, br.borrow_id
#         FROM borrows br
#         JOIN books b ON br.book_id = b.book_id
#         WHERE br.user_id = %s AND br.returned = 1  -- Assuming 'returned' indicates the user has returned the book
#     """, (user_id,))
#     borrowed_books = cursor.fetchall()
#
#     if not borrowed_books:
#         print("You haven't borrowed any books or haven't returned them yet.")
#         return
#
#     # Display borrowed books for the user to select
#     print("Books you have borrowed and can review:")
#     for idx, book in enumerate(borrowed_books, start=1):
#         print(f"{idx}. {book[1]}")
#
#     # Ask user to select a book to review
#     while True:
#         try:
#             book_choice = int(prompt_input("Select the number of the book you want to review: "))
#             if 1 <= book_choice <= len(borrowed_books):
#                 selected_book = borrowed_books[book_choice - 1]
#                 book_id, book_title, borrow_id = selected_book
#                 break
#             else:
#                 print("Invalid choice. Please select a valid number.")
#         except ValueError:
#             print("Please enter a valid number.")
#
#     # Prompt for rating and review text
#     while True:
#         try:
#             rating = int(prompt_input("Enter rating (1-5): "))
#             if 1 <= rating <= 5:
#                 break
#             else:
#                 print("Please enter a rating between 1 and 5.")
#         except ValueError:
#             print("Invalid rating. Please enter a number between 1 and 5.")
#
#     review_text = prompt_input("Enter your review: ")
#
#     # Insert the review into the database
#     cursor.execute("""
#         INSERT INTO reviews (user_id, book_id, rating, review_text, borrow_id)
#         VALUES (%s, %s, %s, %s, %s)
#     """, (user_id, book_id, rating, review_text, borrow_id))
#     db.commit()
#
#     print(f"Review added successfully for '{book_title}'.")




# Function for users to view reviews for a book
def view_reviews_u(user_id):
    print_header("Your Borrowed Books")

    # Fetch the list of books borrowed by the user
    cursor.execute("""
        SELECT DISTINCT b.book_id, b.title
        FROM borrows br
        JOIN books b ON br.book_id = b.book_id
        WHERE br.user_id = %s AND br.returned = 1  -- Assuming 'returned' indicates the user has returned the book
    """, (user_id,))
    borrowed_books = cursor.fetchall()

    if not borrowed_books:
        print("You haven't borrowed or returned any books yet.")
        return

    # Display borrowed books for the user
    print("Books you have borrowed:")
    for idx, book in enumerate(borrowed_books, start=1):
        print(f"{idx}. {book[1]}")

    # Ask the user to input a book title to search for reviews
    book_title_input = prompt_input("Enter the book title to view reviews: ")

    # Find the book_id based on the title input
    matching_books = [book for book in borrowed_books if book_title_input.lower() in book[1].lower()]

    if not matching_books:
        print(f"No books matching '{book_title_input}' found in your borrowed history.")
        return

    # Assuming there could be multiple matches, we select the first match
    book_id, book_title = matching_books[0]

    # Fetch reviews for the selected book
    cursor.execute("""
        SELECT r.rating, r.review_text, u.username
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.book_id = %s
    """, (book_id,))
    reviews = cursor.fetchall()

    if reviews:
        print(f"\nReviews for '{book_title}':")
        print(tabulate(reviews, headers=["Rating", "Review", "User"]))
    else:
        print(f"No reviews found for '{book_title}'.")

    input("\nPress Enter to go back...")

# Admin functions to view, edit, and delete reviews
def view_all_reviews():
    print_header("All Reviews")

    # Join the reviews table with users and books to get username and book title
    cursor.execute("""
        SELECT r.review_id, u.username, b.title, r.rating, r.review_text
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        JOIN books b ON r.book_id = b.book_id
    """)
    reviews = cursor.fetchall()

    # Display the reviews with username and book title
    if reviews:
        print(tabulate(reviews, headers=["Review ID", "Username", "Book Title", "Rating", "Review"]))
    else:
        print("No reviews available.")

    input("\nPress Enter to go back...")


def delete_review():
    review_id = prompt_input("Enter review ID to delete: ")
    cursor.execute("DELETE FROM reviews WHERE review_id = %s", (review_id,))
    db.commit()
    print("Review deleted successfully.")

def edit_review():
    review_id = prompt_input("Enter review ID to edit: ")
    new_rating = int(prompt_input("Enter new rating: "))
    new_review_text = prompt_input("Enter new review text: ")
    cursor.execute("""
        UPDATE reviews
        SET rating = %s, review_text = %s
        WHERE review_id = %s
    """, (new_rating, new_review_text, review_id))
    db.commit()
    print("Review updated successfully.")

# Function to search for reviews based on book title
def search_reviews_by_title(title):
    cursor.execute("""
        SELECT r.review_id, r.rating, r.review_text, b.title
        FROM reviews r
        JOIN books b ON r.book_id = b.book_id
        WHERE b.title LIKE %s
    """, ('%' + title + '%',))
    reviews = cursor.fetchall()
    print(tabulate(reviews, headers=["Review ID", "Rating", "Review", "Book Title"]))

#=========================user can add review=========================================

# def add_review_u(user_id):
#     print_header("Add a Review")
#
#     book_name = input("Enter the Book Name: ")
#
#     # Check if the book exists in the borrowed_books table for the given user_id
#     cursor.execute("""
#         SELECT b.book_id
#         FROM borrowed_books bb
#         JOIN books b ON bb.book_id = b.book_id
#         WHERE bb.user_id = %s AND b.title = %s
#     """, (user_id, book_name))
#     result = cursor.fetchone()
#
#     # Ensure that any unread results are fetched
#     cursor.fetchall()
#
#     if result:
#         book_id = result[0]
#         rating = input("Enter your Rating (1-5): ")
#         review_text = input("Enter your Review: ")
#
#         # Insert the review into the reviews table
#         cursor.execute("""
#             INSERT INTO reviews (user_id, book_id, rating, review_text)
#             VALUES (%s, %s, %s, %s)
#         """, (user_id, book_id, rating, review_text))
#
#         # Commit the transaction to save the review
#         db_connection.commit()
#
#         print("Review added successfully!")
#     else:
#         print("You cannot add a review for this book as it does not exist in your borrowed books.")
#
#     input("\nPress Enter to go back...")





#=========================================     Menu for User     =================================================


def user_menu(user_id):
    while True:
        print_header("User Dashboard")
        print("1. List All Books")
        print("2. View Borrowed Books")
        print("3. Add Membership Plan")
        print("4. Search Books")
        print("5. View Reviews")
        # print("6. Add A Review")
        # print("6. Pay Fine")
        print("0. Logout")
        choice = prompt_input("Enter your choice: ")

        if choice == '1':
            list_all_books()
        elif choice == '2':
            view_borrowed_books(user_id)
        elif choice == '3':
            add_membership_plan_user(user_id)
        elif choice == '4':
            # search_books()
            view_book_details_user(user_id)
        elif choice == '5':
            view_reviews(user_id)
        # elif choice == '6':
        #     add_review(user_id)
        # elif choice == '6':
        #     view_fine(user_id)
        elif choice == '0':
            break


# ===================================================Functions for Users===========================================

def view_borrowed_books(user_id):
    print_header("My Borrowed Books")
    cursor.execute("""
        SELECT books.title, borrowed_books.borrow_date, borrowed_books.return_date 
        FROM borrowed_books 
        JOIN books ON borrowed_books.book_id = books.book_id 
        WHERE borrowed_books.user_id = %s
    """, (user_id,))
    rented_books = cursor.fetchall()
    if rented_books:
        print(tabulate(rented_books, headers=["Book Title", "Borrow Date", "Return Date"]))
    else:
        print("No borrowed books found.")
    input("\nPress Enter to go back...")


def search_books():
    print_header("Search Books")
    search_query = prompt_input("Enter book title or author: ")
    cursor.execute("""
        SELECT books.title, authors.author_name, genres.genre_name, books.available_copies
        FROM books
        JOIN authors ON books.author_id = authors.author_id
        JOIN genres ON books.genre_id = genres.genre_id
        WHERE books.title LIKE %s OR authors.author_name LIKE %s
    """, ('%' + search_query + '%', '%' + search_query + '%'))
    results = cursor.fetchall()
    if results:
        print(tabulate(results, headers=["Book Title", "Author", "Genre", "Available Copies"]))
    else:
        print("No books found.")
    input("\nPress Enter to go back...")


# Guest Access Functions
def browse_books():
    print_header("List Available Books")
    cursor.execute("""
        SELECT books.title, authors.author_name, genres.genre_name, books.available_copies
        FROM books
        JOIN authors ON books.author_id = authors.author_id
        JOIN genres ON books.genre_id = genres.genre_id
    """)
    available_books = cursor.fetchall()
    print(tabulate(available_books, headers=["Book Title", "Author", "Genre", "Available Copies"]))
    input("\nPress Enter to go back...")

#view_book_details() for guest users purpose

def view_book_details():
    print_header("View Book Details")
    book_id = prompt_input("Enter the Book ID to view details: ")
    cursor.execute("""
        SELECT books.title, authors.author_name, genres.genre_name, languages.language_name, books.available_copies
        FROM books
        JOIN authors ON books.author_id = authors.author_id
        JOIN genres ON books.genre_id = genres.genre_id
        JOIN languages ON books.language_id = languages.language_id
        WHERE books.book_id = %s
    """, (book_id,))
    book_details = cursor.fetchone()
    if book_details:
        print(tabulate([book_details], headers=["Book Title", "Author", "Genre", "Language", "Available Copies"]))
    else:
        print("Book not found.")
    input("\nPress Enter to go back...")


def view_book_details_user(user_id):
    print_header("View Book Details")
    search_option = prompt_input("Do you want to search by (1) Book ID, (2) Book Title, or (3) Author's Name? ")

    # Perform book search based on user's input
    if search_option == "1":
        book_id = prompt_input("Enter the Book ID to view details: ")
        cursor.execute("""
            SELECT books.book_id, books.title, authors.author_name, genres.genre_name, 
                   languages.language_name, books.available_copies
            FROM books
            JOIN authors ON books.author_id = authors.author_id
            JOIN genres ON books.genre_id = genres.genre_id
            JOIN languages ON books.language_id = languages.language_id
            WHERE books.book_id = %s
        """, (book_id,))
    elif search_option == "2":
        book_title = prompt_input("Enter the Book Title to search: ")
        cursor.execute("""
            SELECT books.book_id, books.title, authors.author_name, genres.genre_name, 
                   languages.language_name, books.available_copies
            FROM books
            JOIN authors ON books.author_id = authors.author_id
            JOIN genres ON books.genre_id = genres.genre_id
            JOIN languages ON books.language_id = languages.language_id
            WHERE books.title LIKE %s
        """, ("%" + book_title + "%",))
    elif search_option == "3":
        author_name = prompt_input("Enter the Author's Name to search: ")
        cursor.execute("""
            SELECT books.book_id, books.title, authors.author_name, genres.genre_name, 
                   languages.language_name, books.available_copies
            FROM books
            JOIN authors ON books.author_id = authors.author_id
            JOIN genres ON books.genre_id = genres.genre_id
            JOIN languages ON books.language_id = languages.language_id
            WHERE authors.author_name LIKE %s
        """, ("%" + author_name + "%",))
    else:
        print("Invalid search option. Please try again.")
        return

    # Fetch and display the book details
    book_details = cursor.fetchall()
    if book_details:
        print(tabulate(book_details,
                       headers=["Book ID", "Book Title", "Author", "Genre", "Language", "Available Copies"]))

        # Prompt user if they want to borrow a book
        borrow_confirm = input("\nWould you like to borrow a book? (y/n): ").strip().lower()
        if borrow_confirm == 'y':
            book_id = input("\nEnter the Book ID of the book you want to borrow: ").strip()
            borrow_book(user_id, book_id)
        else:
            print("You chose not to borrow a book.")
    else:
        print("No books found.")

    input("\nPress Enter to go back...")

#===================================================borrow book()  ====================================================
def borrow_book(user_id, book_id):
    # Check if the book is available for borrowing
    cursor.execute("""
        SELECT available_copies FROM books WHERE book_id = %s
    """, (book_id,))

    result = cursor.fetchone()
    if not result:
        print("Invalid Book ID. Please try again.")
        return

    available_copies = result[0]

    if available_copies > 0:
        # Decrease the number of available copies
        cursor.execute("""
            UPDATE books SET available_copies = available_copies - 1 WHERE book_id = %s
        """, (book_id,))

        # Record the book borrowing
        borrow_date = datetime.now().date()
        cursor.execute("""
            INSERT INTO borrowed_books (user_id, book_id, borrow_date, return_date)
            VALUES (%s, %s, %s, NULL)
        """, (user_id, book_id, borrow_date))

        db.commit()
        print("The book you selected for borrowing is ready for payment. \nYou can pay now.")

        # If any payment (such as a borrowing fee) is required, lead to payment process
        # For this example, we assume there's a fixed borrowing fee (e.g., ₹50)
        borrowing_fee = 50
        process_payment(user_id, borrowing_fee)
    else:
        print("Sorry, no copies of this book are available at the moment.")

    input("\nPress Enter to continue...")

#====================================add review --> for users to add review  =============================


def add_review_user(user_id):
    print_header("Add Review")

    # Get list of books borrowed by the user
    cursor.execute("""
        SELECT borrowed_books.book_id, books.title
        FROM borrowed_books
        JOIN books ON borrowed_books.book_id = books.book_id
        WHERE borrowed_books.user_id = %s AND borrowed_books.return_date IS NOT NULL
    """, (user_id,))

    borrowed_books = cursor.fetchall()
    if not borrowed_books:
        print("You haven't borrowed any books yet.")
        return

    # Display list of borrowed books
    print("\nSelect a book to review:")
    for i, book in enumerate(borrowed_books):
        print(f"{i+1}. {book[1]}")

    book_choice = int(input("Enter the number of the book: ")) - 1
    book_id = borrowed_books[book_choice][0]

    # Get rating and review text from user
    rating = int(input("Enter your rating (1-5): "))
    review_text = input("Enter your review: ")

    # Insert review into the reviews table
    cursor.execute("""
        INSERT INTO reviews (user_id, book_id, rating, review_text)
        VALUES (%s, %s, %s, %s)
    """, (user_id, book_id, rating, review_text))
    db.commit()

    print("Review added successfully!")

#==========================================view review  for users ======================================================
def view_reviews(book_id):
    print_header("View Reviews")

    # Get reviews for the specified book
    cursor.execute("""
        SELECT users.username, reviews.rating, reviews.review_text
        FROM reviews
        JOIN users ON reviews.user_id = users.user_id
        WHERE reviews.book_id = %s
    """, (book_id,))

    reviews = cursor.fetchall()
    if not reviews:
        print("No reviews found for this book.")
        return

    # Display reviews
    print("\nReviews:")
    for review in reviews:
        print(f"Username: {review[0]}")
        print(f"Rating: {review[1]}/5")
        print(f"Review: {review[2]}\n")

    print("Press Enter to continue...")
    input()


#=======================================search option for reviewing for users==========================

def search_book_users():
    print_header("Search Book")

    # Get search query from user
    query = input("Enter book title or author: ")

    # Search for books
    cursor.execute("""
        SELECT b.book_id, b.title, a.author_name
        FROM books b
        JOIN authors a ON b.author_id = a.author_id
        WHERE b.title LIKE %s OR a.author_name LIKE %s
    """, (f"%{query}%", f"%{query}%"))

    books = cursor.fetchall()
    if not books:
        print("No books found.")
        return

    # Display search results
    print("\nSearch Results:")
    for i, book in enumerate(books):
        print(f"{i+1}. {book[1]} by {book[2]}")

    book_choice = int(input("Enter the number of the book: ")) - 1
    book_id = books[book_choice][0]

    # Display book details and reviews
    print(f"\nBook Title: {books[book_choice][1]}")
    print(f"Author: {books[book_choice][2]}")
    print("Reviews:")
    view_reviews(book_id)

#============================================ search book for review ==================================

def search_book_review():
    print_header("Search Book")

    # Get search query from user
    query = input("Enter book title or author: ")

    # Search for books
    cursor.execute("""
        SELECT book_id, title, author
        FROM books
        WHERE title LIKE %s OR author LIKE %s
    """, (f"%{query}%", f"%{query}%"))

    books = cursor.fetchall()
    if not books:
        print("No books found.")
        return

    # Display search results
    print("\nSearch Results:")
    for i, book in enumerate(books):
        print(f"{i+1}. {book[1]} by {book[2]}")

    book_choice = int(input("Enter the number of the book: ")) - 1
    book_id = books[book_choice][0]

    # Display book details and reviews
    print(f"\nBook Title: {books[book_choice][1]}")
    print(f"Author: {books[book_choice][2]}")
    print("Reviews:")
    view_reviews(book_id)


#===============================================  guest  ====================================================4

def view_book_details_guest():
    print_header("View Book Details")

    # Prompt user to choose a search option
    search_option = prompt_input("Do you want to search by (1) Book ID, (2) Book Title, or (3) Author's Name? ")

    # If searching by Book ID
    if search_option == "1":
        while True:
            book_id = prompt_input("Enter the Book ID to view details: ")
            if not book_id.isdigit():
                print("Invalid input. Book ID must be numeric. Please try again.")
            else:
                break  # Valid input, proceed to query

        cursor.execute("""
            SELECT books.title, authors.author_name, genres.genre_name, languages.language_name, books.available_copies
            FROM books
            JOIN authors ON books.author_id = authors.author_id
            JOIN genres ON books.genre_id = genres.genre_id
            JOIN languages ON books.language_id = languages.language_id
            WHERE books.book_id = %s
        """, (book_id,))

    # If searching by Book Title
    elif search_option == "2":
        while True:
            book_title = prompt_input("Enter the Book Title to search: ")
            if not book_title.replace(' ', '').isalpha():
                print("Invalid input. Book Title must contain only alphabetic characters and spaces. Please try again.")
            else:
                break  # Valid input, proceed to query

        cursor.execute("""
            SELECT books.title, authors.author_name, genres.genre_name, languages.language_name, books.available_copies
            FROM books
            JOIN authors ON books.author_id = authors.author_id
            JOIN genres ON books.genre_id = genres.genre_id
            JOIN languages ON books.language_id = languages.language_id
            WHERE books.title LIKE %s
        """, ("%" + book_title + "%",))

    # If searching by Author's Name
    elif search_option == "3":
        author_name = prompt_input("Enter the Author's Name to search: ")

        cursor.execute("""
                SELECT books.title, authors.author_name, genres.genre_name, languages.language_name, books.available_copies
                FROM books
                JOIN authors ON books.author_id = authors.author_id
                JOIN genres ON books.genre_id = genres.genre_id
                JOIN languages ON books.language_id = languages.language_id
                WHERE authors.author_name LIKE %s
            """, ("%" + author_name + "%",))

        # Handle invalid search option
    else:
        print("Invalid search option. Please try again.")
        return

        # Fetch and display book details
    book_details = cursor.fetchall()
    if book_details:
        print(tabulate(book_details, headers=["Book Title", "Author", "Genre", "Language", "Available Copies"]))
    else:
        print("No books found.")

    # Prompt to go back
    input("\nPress Enter to go back...")


def calculate_fine(days_overdue):
    if days_overdue <= 3:
        return days_overdue * 10
    elif 4 <= days_overdue <= 7:
        return days_overdue * 20
    elif 8 <= days_overdue <= 14:
        return days_overdue * 30
    else:
        return min(days_overdue * 40, 500)  # Max fine is ₹500


def view_fine(user_id):
    print_header("Pay Fine")

    # Check if user has overdue books
    cursor.execute("""
        SELECT borrowed_books.book_id, books.title, borrowed_books.borrow_date, borrowed_books.return_date
        FROM borrowed_books
        JOIN books ON borrowed_books.book_id = books.book_id
        WHERE borrowed_books.user_id = %s AND borrowed_books.return_date IS NOT NULL
    """, (user_id,))

    borrowed_books = cursor.fetchall()
    if not borrowed_books:
        print("No overdue books or fines for this user.")
        return

    total_fine = 0
    overdue_books = []

    for book in borrowed_books:
        return_date = book[3]
        if return_date < datetime.now().date():
            days_overdue = (datetime.now().date() - return_date).days
            fine = calculate_fine(days_overdue)
            total_fine += fine
            overdue_books.append((book[1], days_overdue, fine))

    if total_fine == 0:
        print("No fines due for this user.")
        return

    # Display overdue books and fines
    print("\nOverdue Books and Fines:")
    for book in overdue_books:
        print(f"Book: {book[0]}, Days Overdue: {book[1]}, Fine: ₹{book[2]}")

    print(f"\nTotal Fine Due: ₹{total_fine}")

    # Payment confirmation
    confirm = input("\nWould you like to pay the fine now? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Payment canceled.")
        return

    # Call the payment process function
    process_payment(user_id, total_fine)

    # Insert fine into the fines table after payment
    cursor.execute("""
        INSERT INTO fines (user_id, amount)
        VALUES (%s, %s)
    """, (user_id, total_fine))
    db.commit()

    print("Fine has been successfully paid.")
    input("\nPress Enter to go back...")

#==================================================add membership plan for users==================================



def add_membership_plan_user(user_id):
    print_header("View Membership Plans")

    # Check if the user has an active membership plan
    cursor.execute("""
        SELECT membership_plans.plan_name, membership_plans.plan_duration, membership_plans.plan_price, 
               membership_plans.description, membership_plans.max_borrowings, membership_plans.borrowing_period, 
               membership_plans.renewal_fee, membership_plans.late_fee
        FROM users
        JOIN membership_plans ON users.membership_plan_id = membership_plans.plan_id
        WHERE users.user_id = %s AND membership_plans.is_active = TRUE
    """, (user_id,))

    active_plan = cursor.fetchone()

    # If the user has an active membership plan, display it
    if active_plan:
        print("\nYour Current Active Membership Plan:")
        print(tabulate([active_plan], headers=[
            "Plan Name", "Duration (days)", "Price (₹)", "Description",
            "Max Borrowings", "Borrowing Period (days)", "Renewal Fee (₹)", "Late Fee (₹)"
        ]))

        # Ask the user if they want to switch to a new membership plan
        switch_plan = input("\nWould you like to switch to a new membership plan? (y/n): ").strip().lower()
        if switch_plan != 'y':
            print("You chose to keep your current membership.")
            return
    else:
        print("You don't have an active membership plan.")

    # Display available membership plans if no active plan or if user wants to switch
    cursor.execute("""
        SELECT plan_id, plan_name, plan_duration, plan_price, description, benefits, 
               max_borrowings, borrowing_period, renewal_fee, late_fee
        FROM membership_plans
        WHERE is_active = TRUE
    """)

    plans = cursor.fetchall()
    if plans:
        print("\nAvailable Membership Plans:")
        print(tabulate(plans, headers=[
            "Plan ID", "Plan Name", "Duration (days)", "Price (₹)", "Description", "Benefits",
            "Max Borrowings", "Borrowing Period (days)", "Renewal Fee (₹)", "Late Fee (₹)"
        ]))

        # Prompt user to select a new membership plan
        plan_id = input("\nEnter the Plan ID of the membership you want to choose: ").strip()

        # Check if the plan exists
        cursor.execute("""
            SELECT plan_price
            FROM membership_plans
            WHERE plan_id = %s AND is_active = TRUE
        """, (plan_id,))
        selected_plan = cursor.fetchone()

        if not selected_plan:
            print("Invalid Plan ID. Please try again.")
            return

        # Extract plan price for the payment
        plan_price = selected_plan[0]

        # Confirm the user's choice
        confirm = input(
            f"\nYou selected Plan ID {plan_id} with a price of ₹{plan_price}. Do you want to proceed with payment? (y/n): ").strip().lower()

        if confirm == 'y':
            # Proceed to payment using the updated process_payment function with validations
            if process_payment_all(user_id, plan_price):  # Only if payment succeeds
                # After successful payment, update the user's membership plan
                cursor.execute("""
                    UPDATE users
                    SET membership_plan_id = %s, updated_at = NOW()
                    WHERE user_id = %s
                """, (plan_id, user_id))
                db.commit()

                print("Membership plan added successfully!")
        else:
            print("Membership selection canceled.")
    else:
        print("No active membership plans available.")

    input("\nPress Enter to go back...")




#==========================================  process_payment()  =================================================

def process_payment_all(user_id, total_fine):
    """Handles payment options and processes the selected payment."""
    print("\nSelect Payment Method:")
    print("1. Net Banking")
    print("2. UPI Payment")
    print("3. Credit Card")
    payment_method = input("Enter the number corresponding to your payment method: ").strip()

    # Net Banking
    if payment_method == '1':
        print("\n--- Net Banking ---")
        bank_name = input("Enter Bank Name: ").strip()

        # Validate account number (assuming valid account numbers have 10-18 digits)
        account_number = input("Enter Account Number: ").strip()
        if not account_number.isdigit() or not (10 <= len(account_number) <= 18):
            print("Invalid Account Number. Please enter a valid account number with 10-18 digits.")
            return False  # Payment failed

        print(f"Processing payment of ₹{total_fine} via Net Banking...")

    # UPI Payment
    elif payment_method == '2':
        print("\n--- UPI Payment ---")

        # Validate UPI ID (general format: something@bank, must include '@')
        upi_id = input("Enter UPI ID (example: user@bank): ").strip()
        if not re.match(r'^\w+@\w+$', upi_id):
            print("Invalid UPI ID format. Please use the format 'user@bank'.")
            return False  # Payment failed

        upi_name = input("Enter UPI Account Name: ").strip()
        if not upi_name.isalpha():
            print("Invalid UPI Account Name. Name should only contain alphabetic characters.")
            return False  # Payment failed

        print(f"Processing payment of ₹{total_fine} via UPI ID: {upi_id} ({upi_name})...")

    # Credit Card Payment
    elif payment_method == '3':
        print("\n--- Credit Card Payment ---")

        # Validate card number (must be 16 digits)
        card_number = input("Enter Card Number: ").strip()
        if not re.match(r'^\d{16}$', card_number):
            print("Invalid Card Number. Please enter a valid 16-digit card number.")
            return False  # Payment failed

        # Validate expiry date (MM/YY format)
        expiry_date = input("Enter Expiry Date (MM/YY): ").strip()
        if not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', expiry_date):
            print("Invalid Expiry Date. Please enter in MM/YY format.")
            return False  # Payment failed

        # Validate CVV (must be 3 digits)
        cvv = input("Enter CVV: ").strip()
        if not re.match(r'^\d{3}$', cvv):
            print("Invalid CVV. Please enter a valid 3-digit CVV.")
            return False  # Payment failed

        print(f"Processing payment of ₹{total_fine} via Credit Card...")

    else:
        print("Invalid payment method. Payment canceled.")
        return False  # Payment failed

    # Confirming payment success only if all validations are passed
    print("\nPayment processing...")
    print("Payment successful!")
    return True  # Payment succeeded




def process_payment(user_id, total_fine):
    """Handles payment options and processes the selected payment."""
    print("\nSelect Payment Method:")
    print("1. Net Banking")
    print("2. UPI Payment")
    print("3. Credit Card")
    payment_method = input("Enter the number corresponding to your payment method: ").strip()

    # Net Banking
    if payment_method == '1':
        print("\n--- Net Banking ---")
        bank_name = input("Enter Bank Name: ").strip()

        # Validate account number (assuming valid account numbers have 10-18 digits)
        account_number = input("Enter Account Number: ").strip()
        if not account_number.isdigit() or not (10 <= len(account_number) <= 18):
            print("Invalid Account Number. Please enter a valid account number with 10-18 digits.")
            return

        print(f"Processing payment of ₹{total_fine} via Net Banking...")

    # UPI Payment
    elif payment_method == '2':
        print("\n--- UPI Payment ---")

        # Validate UPI ID (general format: something@bank, must include '@')
        upi_id = input("Enter UPI ID (example: user@bank): ").strip()
        if not re.match(r'^\w+@\w+$', upi_id):
            print("Invalid UPI ID format. Please use the format 'user@bank'.")
            return

        upi_name = input("Enter UPI Account Name: ").strip()
        if not upi_name.isalpha():
            print("Invalid UPI Account Name. Name should only contain alphabetic characters.")
            return

        print(f"Processing payment of ₹{total_fine} via UPI ID: {upi_id} ({upi_name})...")

    # Credit Card Payment
    elif payment_method == '3':
        print("\n--- Credit Card Payment ---")

        # Validate card number (must be 16 digits)
        card_number = input("Enter Card Number: ").strip()
        if not re.match(r'^\d{16}$', card_number):
            print("Invalid Card Number. Please enter a valid 16-digit card number.")
            return

        # Validate expiry date (MM/YY format)
        expiry_date = input("Enter Expiry Date (MM/YY): ").strip()
        if not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', expiry_date):
            print("Invalid Expiry Date. Please enter in MM/YY format.")
            return

        # Validate CVV (must be 3 digits)
        cvv = input("Enter CVV: ").strip()
        if not re.match(r'^\d{3}$', cvv):
            print("Invalid CVV. Please enter a valid 3-digit CVV.")
            return

        print(f"Processing payment of ₹{total_fine} via Credit Card...")

    else:
        print("Invalid payment method. Payment canceled.")
        return

    # Confirming payment success
    print("\nPayment processing...")
    print("Payment successful!")



# ============================================  Main function  ===============================================
def main():
    while True:
        print_header("Welcome to the Library Management System")
        print("1. Login")
        print("2. Register")
        print("3. Guest Access")
        print("0. Exit")
        choice = prompt_input("Enter your choice: ")

        if choice == '1':
            login()
        elif choice == '2':
            register()
        elif choice == '3':
            while True:
                print_header("Guest Access")
                print("1. List Available Books")
                print("2. Browse Books")
                print("3. View Membership Details")
                print("0. Back")
                guest_choice = prompt_input("Enter your choice: ", allow_back=True)

                if guest_choice == '1':
                    browse_books()
                elif guest_choice == '2':
                    view_book_details_guest()
                elif guest_choice == '3':
                    view_membership_plan_guest()
                elif guest_choice is None:
                    break
        elif choice == '0':
            break


if __name__ == '__main__':
    main()


