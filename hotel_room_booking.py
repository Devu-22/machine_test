import mysql.connector
import re
import time
from datetime import datetime
import bcrypt

# Connect to MySQL database
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Devu@22112002',
    database='machine_test'
)
cursor = db.cursor()


# SQL Tables creation
def create_tables():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price_per_day DECIMAL(10, 2) NOT NULL,
            price_per_hour DECIMAL(10, 2)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            room_no VARCHAR(255) NOT NULL,
            category_id INT NOT NULL,
            status ENUM('occupied', 'unoccupied') DEFAULT 'unoccupied',
            FOREIGN KEY (category_id) REFERENCES category(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(255) NOT NULL,
            last_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            phone VARCHAR(10) NOT NULL,
            username VARCHAR(20) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id VARCHAR(255) NOT NULL UNIQUE,
            customer_id INT NOT NULL,
            room_id INT NOT NULL,
            booking_date DATE NOT NULL,
            occupancy_date DATE NOT NULL,
            no_of_days INT NOT NULL,
            advance_received DECIMAL(10, 2) NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        );
    """)

    db.commit()
    print("Tables created successfully!")


def insert_sample_data():
    # Insert categories
    cursor.execute("""
        INSERT INTO category (name, price_per_day, price_per_hour)
        VALUES
        ('Single', 50.00, 10.00),
        ('Double', 75.00, 15.00),
        ('Suite', 150.00, 25.00)
    """)

    # Insert rooms
    cursor.execute("""
        INSERT INTO rooms (room_no, category_id, status)
        VALUES
        ('101', 1, 'unoccupied'),
        ('102', 1, 'unoccupied'),
        ('201', 2, 'unoccupied'),
        ('202', 2, 'occupied'),
        ('301', 3, 'unoccupied'),
        ('302', 3, 'occupied')
    """)

    # Insert customers
    cursor.execute("""
        INSERT INTO customers (first_name, last_name, email, phone, username, password)
        VALUES
        ('John', 'Doe', 'john.doe@example.com', '9876543210', 'john_doe', 'password1'),
        ('Jane', 'Doe', 'jane.doe@example.com', '9876543211', 'jane_doe', 'password2'),
        ('Alice', 'Smith', 'alice.smith@example.com', '9876543212', 'alice_smith', 'password3')
    """)

    # Insert bookings
    cursor.execute("""
        INSERT INTO bookings (booking_id, customer_id, room_id, booking_date, occupancy_date, no_of_days, advance_received, total_amount)
        VALUES
        ('BKG123', 1, 1, '2024-08-01', '2024-08-10', 5, 100.00, 250.00),
        ('BKG124', 2, 4, '2024-08-02', '2024-08-15', 3, 150.00, 225.00),
        ('BKG125', 3, 6, '2024-08-05', '2024-08-18', 7, 200.00, 1050.00)
    """)

    db.commit()


# Call the function to insert sample data
# insert_sample_data()


# Utility function to generate a Booking ID
def generate_booking_id():
    prefix = "BK"
    suffix = str(time.time_ns())[-5:]
    return prefix + suffix


# 1. Display the Category-wise list of rooms and their Rate per day
def display_rooms_by_category():
    query = """SELECT c.name AS category, r.room_no, c.price_per_day, c.price_per_hour 
               FROM rooms r 
               JOIN category c ON r.category_id = c.id 
               ORDER BY c.name;"""
    cursor.execute(query)
    rooms = cursor.fetchall()
    for room in rooms:
        category, room_no, rate_per_day, rate_per_hour = room
        if rate_per_hour:
            print(
                f"Room No: {room_no}, Category: {category}, Rate per Day: {rate_per_day}, Rate per Hour: {rate_per_hour}")
        else:
            print(f"Room No: {room_no}, Category: {category}, Rate per Day: {rate_per_day}")


# 2. List all rooms occupied for the next two days
def list_occupied_rooms_next_two_days():
    query = """SELECT rooms.room_no, bookings.occupancy_date 
               FROM rooms 
               JOIN bookings ON rooms.id = bookings.room_id 
               WHERE bookings.occupancy_date BETWEEN CURDATE() AND CURDATE() + INTERVAL 2 DAY"""
    cursor.execute(query)
    occupied_rooms = cursor.fetchall()
    for room_no, occupancy_date in occupied_rooms:
        print(f"Room No: {room_no}, Occupied on: {occupancy_date}")


# 3. Display the list of all rooms in their increasing order of rate per day
def display_rooms_by_rate():
    query = """SELECT r.room_no, c.name AS category, c.price_per_day AS rate_per_day 
               FROM rooms r 
               JOIN category c ON r.category_id = c.id 
               ORDER BY c.price_per_day ASC"""
    cursor.execute(query)
    rooms = cursor.fetchall()
    for room_no, category, rate_per_day in rooms:
        print(f"Room No: {room_no}, Category: {category}, Rate per Day: {rate_per_day}")


# 4. Search Rooms based on BookingID and display the customer details
def search_room_by_booking_id(booking_id):
    query = """SELECT rooms.room_no, customers.first_name, customers.last_name, bookings.booking_date
               FROM bookings 
               JOIN rooms ON bookings.room_id = rooms.id 
               JOIN customers ON bookings.customer_id = customers.id 
               WHERE bookings.booking_id = %s"""
    cursor.execute(query, (booking_id,))
    result = cursor.fetchone()
    if result:
        room_no, first_name, last_name, booking_date = result
        print(
            f"Booking ID: {booking_id}, Room No: {room_no}, Customer: {first_name} {last_name}, Booking Date: {booking_date}")
    else:
        print("No booking found with that ID.")


# 5. Display rooms which are not booked
def display_unbooked_rooms():
    query = """SELECT r.room_no, c.name AS category, c.price_per_day, c.price_per_hour
               FROM rooms r
               JOIN category c ON r.category_id = c.id
               WHERE r.status = 'unoccupied'"""
    cursor.execute(query)
    unbooked_rooms = cursor.fetchall()
    for room_no, category, price_per_day, price_per_hour in unbooked_rooms:
        print(
            f"Room No: {room_no}, Category: {category}, Rate per day: {price_per_day}, Rate per hour: {price_per_hour if price_per_hour else 'N/A'}")


# 6. Update room when the customer leaves to Unoccupied
def update_room_to_unoccupied(room_no):
    query = "UPDATE rooms SET status = 'unoccupied' WHERE room_no = %s"
    cursor.execute(query, (room_no,))
    db.commit()
    print(f"Room {room_no} status updated to unoccupied.")


# 7. Store all records in file and display from file
def store_records_in_file():
    query = "SELECT * FROM bookings"
    cursor.execute(query)
    bookings = cursor.fetchall()
    with open('bookings.txt', 'w') as f:
        for booking in bookings:
            f.write(str(booking) + '\n')
    print("Records stored in bookings.txt")


def display_records_from_file():
    try:
        with open('bookings.txt', 'r') as f:
            records = f.readlines()
            for record in records:
                print(record.strip())
    except FileNotFoundError:
        print("No records found in file.")


# 8. Register a new customer
def register_customer(first_name, last_name, email, phone, username, password):
    try:
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")

        # Validate phone number format
        if not re.match(r"^\d{10}$", phone):
            raise ValueError("Phone number should be 10 digits")

        # Validate username
        if not re.match(r"^[a-zA-Z0-9_]{5,20}$", username):
            raise ValueError(
                "Username should be 5-20 characters long and contain only letters, numbers, or underscores")

        # Validate password
        if len(password) < 8:
            raise ValueError("Password should be at least 8 characters long")

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert new customer into the database
        query = """INSERT INTO customers (first_name, last_name, email, phone, username, password)
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (first_name, last_name, email, phone, username, hashed_password))
        db.commit()
        print("Customer registered successfully!")
    except mysql.connector.IntegrityError as e:
        if 'username' in str(e):
            print("Error: Username already exists.")
        elif 'email' in str(e):
            print("Error: Customer with this email already exists.")
    except ValueError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# 9. Pre-book a room
def pre_book_room(customer_id, room_no, occupancy_date, no_of_days, advance_received):
    try:
        # Query to get room details including category and rates
        query_room = """SELECT r.id, c.price_per_day, c.price_per_hour, c.name 
                        FROM rooms r 
                        JOIN category c ON r.category_id = c.id 
                        WHERE r.room_no = %s"""
        cursor.execute(query_room, (room_no,))
        room = cursor.fetchone()
        if not room:
            raise ValueError("Invalid room number")

        room_id, rate_per_day, rate_per_hour, category = room
        booking_id = generate_booking_id()

        # Calculate the total amount based on room category
        if category in ('convention_hall', 'ballroom'):
            total_amount = (rate_per_hour * no_of_days * 24) + 100  # Include tax, housekeeping, misc. fixed charges
        else:
            total_amount = (rate_per_day * no_of_days) + 100  # Include tax, housekeeping, misc. fixed charges

        # Insert booking record into the bookings table
        query_booking = """INSERT INTO bookings (booking_id, customer_id, room_id, booking_date, occupancy_date, no_of_days, advance_received, total_amount)
                           VALUES (%s, %s, %s, CURDATE(), %s, %s, %s, %s)"""
        cursor.execute(query_booking,
                       (booking_id, customer_id, room_id, occupancy_date, no_of_days, advance_received, total_amount))

        # Update the room status to 'occupied'
        query_update_room = "UPDATE rooms SET status = 'occupied' WHERE id = %s"
        cursor.execute(query_update_room, (room_id,))
        db.commit()

        print(f"Room {room_no} pre-booked successfully with Booking ID: {booking_id}")
    except ValueError as e:
        print(f"Error: {e}")


# 10. Display Booking History for a Customer
def display_booking_history(customer_id):
    query = """SELECT bookings.booking_id, rooms.room_no, bookings.occupancy_date, bookings.no_of_days, bookings.total_amount
               FROM bookings 
               JOIN rooms ON bookings.room_id = rooms.id 
               WHERE bookings.customer_id = %s"""
    cursor.execute(query, (customer_id,))
    history = cursor.fetchall()
    for booking_id, room_no, occupancy_date, no_of_days, total_amount in history:
        print(
            f"Booking ID: {booking_id}, Room No: {room_no}, Occupancy Date: {occupancy_date}, Duration: {no_of_days} days, Total Amount: {total_amount}")




def admin_login():
    username = input("Enter Admin Username: ")
    password = input("Enter Admin Password: ")

    # Query to find the admin user
    query = "SELECT password FROM admin WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()

    if result:
        stored_password = result[0]

        # Check if the entered password matches the stored hashed password
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            print("Login successful!")
            admin_menu()  # Call the admin menu function after successful login
        else:
            print("Incorrect password. Please try again.")
    else:
        print("Admin user not found. Please check your username and try again.")


# Admin Functionalities
def admin_menu():
    while True:
        print("\nAdmin Menu")
        print("1. View Rooms by Category")
        print("2. List Occupied Rooms for Next Two Days")
        print("3. List Rooms by Rate")
        print("4. Search Room by Booking ID")
        print("5. View Unbooked Rooms")
        print("6. Update Room Status to Unoccupied")
        print("7. Store Records in File")
        print("8. Display Records from File")
        print("9. Exit")

        choice = input("Enter your choice: ")
        if choice == '1':
            display_rooms_by_category()
        elif choice == '2':
            list_occupied_rooms_next_two_days()
        elif choice == '3':
            display_rooms_by_rate()
        elif choice == '4':
            booking_id = input("Enter Booking ID: ")
            search_room_by_booking_id(booking_id)
        elif choice == '5':
            display_unbooked_rooms()
        elif choice == '6':
            room_no = input("Enter Room No to update to Unoccupied: ")
            update_room_to_unoccupied(room_no)
        elif choice == '7':
            store_records_in_file()
        elif choice == '8':
            display_records_from_file()
        elif choice == '9':
            break
        else:
            print("Invalid choice. Please try again.")


def customer_menu(customer_id):
    while True:
        print("\nCustomer Menu")
        print("1. View Rooms by Category")
        print("2. View Rooms by Rate")
        print("3. View Unbooked Rooms")
        print("4. Pre-book a Room")
        print("5. View Booking History")
        print("6. Make a Payment")
        print("7. Logout")

        choice = input("Enter your choice: ")
        if choice == '1':
            display_rooms_by_category()
        elif choice == '2':
            display_rooms_by_rate()
        elif choice == '3':
            display_unbooked_rooms()
        elif choice == '4':
            room_no = input("Enter Room No: ")
            occupancy_date = input("Enter Occupancy Date (YYYY-MM-DD): ")
            no_of_days = int(input("Enter Number of Days: "))
            advance_received = float(input("Enter Advance Received: "))
            pre_book_room(customer_id, room_no, occupancy_date, no_of_days, advance_received)
        elif choice == '5':
            display_booking_history(customer_id)
        elif choice == '6':
            booking_id = input("Enter Booking ID for Payment: ")
            make_payment(booking_id)
        elif choice == '7':
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")




# Validate card details
def validate_card_details(card_number, expiry_date, cvv):
    print(f"Debug: card_number={card_number}, expiry_date={expiry_date}, cvv={cvv}")  # Debug print

    if not re.match(r"^\d{10,15}$", card_number):
        raise ValueError("Invalid card number. Must be between 10 to 15 digits.")

    try:
        exp_date = datetime.strptime(expiry_date, "%m/%y")
        if exp_date < datetime.now():
            raise ValueError("Card expiry date is invalid or expired.")
    except ValueError:
        raise ValueError("Invalid expiry date format. Use MM/YY.")

    if not re.match(r"^\d{3}$", cvv):
        raise ValueError("Invalid CVV. Must be 3 digits.")

# Make a payment for a booking
def make_payment(booking_id):
    try:
        query = "SELECT total_amount, advance_received FROM bookings WHERE booking_id = %s"
        cursor.execute(query, (booking_id,))
        result = cursor.fetchone()

        if result:
            total_amount, advance_received = result
            remaining_amount = total_amount - advance_received

            if remaining_amount > 0:
                card_number = input("Enter your card number (10-15 digits): ")
                expiry_date = input("Enter your card expiry date (MM/YY): ")
                cvv = input("Enter your CVV (3 digits): ")

                try:
                    validate_card_details(card_number, expiry_date, cvv)
                except ValueError as e:
                    print(f"Payment failed: {e}")
                    return

                payment = float(input(f"Total amount due: {remaining_amount}. Enter payment amount: "))
                if payment >= remaining_amount:
                    query_update = "UPDATE bookings SET advance_received = %s WHERE booking_id = %s"
                    cursor.execute(query_update, (total_amount, booking_id))
                    db.commit()
                    print("Payment successful! Booking is now fully paid.")
                else:
                    print("Payment amount is less than the due amount.")
            else:
                print("No amount is due. The booking is already fully paid.")
        else:
            print("Invalid Booking ID.")
    except ValueError:
        print("Invalid input. Please enter a valid number.")

# Add additional charges
def add_additional_charges(charge_name, amount):
    try:
        query = "INSERT INTO additional_charges (charge_name, amount) VALUES (%s, %s)"
        cursor.execute(query, (charge_name, amount))
        db.commit()
        print("Additional charges added successfully!")
    except Exception as e:
        print(f"Error adding charges: {e}")

# Get customer ID based on username
def get_customer_id(username):
    try:
        query = "SELECT id FROM customers WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None

# User login
def login(username, password):
    try:
        query = "SELECT password FROM customers WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result:
            hashed_password = result[0]
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                return True
        return False
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return False

# Main function to run the system
# Main function to run the system
def main_menu():
    while True:
        print("\nHotel Booking System")
        print("1. Register Customer")
        print("2. Login (Admin/Customer)")
        print("3. View Rooms and Rates (Guest)")
        print("4. Exit")

        choice = input("Enter your choice: ")
        if choice == '1':
            first_name = input("Enter First Name: ")
            last_name = input("Enter Last Name: ")
            email = input("Enter Email: ")
            phone = input("Enter Phone Number: ")
            username = input("Create Username: ")
            password = input("Create Password: ")
            register_customer(first_name, last_name, email, phone, username, password)

            # Retrieve the customer_id after registration
            customer_id = get_customer_id(username)
            if customer_id:
                customer_menu(customer_id)
            else:
                print("Error retrieving customer ID after registration.")
        elif choice == '2':
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            user_type = input("Are you an Admin or Customer? (admin/customer): ").lower()

            if user_type == 'admin':
                if username == 'Devu' and password == 'Devu@123':
                    admin_menu()
                else:
                    print("Invalid username or password.")
            elif user_type == 'customer':
                if login(username, password):
                    customer_id = get_customer_id(username)
                    if customer_id:
                        customer_menu(customer_id)
                    else:
                        print("Customer ID not found.")
                else:
                    print("Invalid username or password.")
            else:
                print("Invalid user type. Please try again.")
        elif choice == '3':
            display_unbooked_rooms()
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main_menu()






