from flask import Flask, render_template, request, redirect, url_for, flash
from decimal import Decimal
from datetime import date
import mysql.connector
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from werkzeug.security import generate_password_hash

import time
import threading

# Flask app setup
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Set a secret key for sessions and flash messages

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'path_to_json_file.json'

# Update these with your actual Google Sheet IDs and range names
SPREADSHEET_ID_PRODUCTS = 'spreadsheetid'
RANGE_NAME_PRODUCTS = 'Sheet1!A:D'  # Ensure this range is correct

SPREADSHEET_ID_USERS = 'spread_sheet_id'
RANGE_NAME_USERS = 'Sheet2!A:C'  # Ensure this range is correct

SPREADSHEET_ID_STAFF = 'spread_sheet_id'
RANGE_NAME_STAFF = 'Sheet3!A:D'  # Ensure this range is correct

logging.basicConfig(level=logging.INFO)

# Function to establish MySQL connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",  # Update this with your MySQL password
        database="inventory_db"  # Update this with your MySQL database name
    )

def fetch_products():
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    cursor.execute("SELECT product_name, quantity, description, last_updated FROM products")
    products = cursor.fetchall()
    cursor.close()
    db_conn.close()
    return products

def fetch_users():
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    cursor.execute("SELECT username, role FROM users")
    users = cursor.fetchall()
    cursor.close()
    db_conn.close()
    return users

def fetch_staff():
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT staff.id, users.username, staff.position, staff.salary
        FROM staff JOIN users ON staff.user_id = users.id
    """)
    staff = cursor.fetchall()
    cursor.close()
    db_conn.close()
    return staff

@app.route('/')
def index():
    products = fetch_products()
    return render_template('index.html', products=products)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        product_name = request.form['product_name']
        quantity = request.form['quantity']
        description = request.form['description']
        last_updated = date.today()

        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        cursor.execute("""
            INSERT INTO products (product_name, quantity, description, last_updated)
            VALUES (%s, %s, %s, %s)
        """, (product_name, quantity, description, last_updated))
        db_conn.commit()

        cursor.close()
        db_conn.close()

        sync_products_to_google_sheets()
        flash('Item added and synced successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_item.html')
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        # Remove the method argument to use the default hashing
        hashed_password = generate_password_hash(password)  
        cursor.execute("""
            INSERT INTO users (username, password, role) VALUES (%s, %s, %s)
        """, (username, hashed_password, role))
        db_conn.commit()

        cursor.close()
        db_conn.close()

        sync_users_to_google_sheets()  # Optional: Syncing to Google Sheets if needed
        flash('User registered successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_user.html')

@app.route('/add_staff', methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
        username = request.form['username']
        position = request.form['position']
        salary = request.form['salary']

        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            cursor.execute("""
                INSERT INTO staff (user_id, position, salary) VALUES (%s, %s, %s)
            """, (user[0], position, salary))
            db_conn.commit()
            flash('Staff added successfully!', 'success')
        else:
            flash('User not found!', 'danger')

        cursor.close()
        db_conn.close()

        sync_staff_to_google_sheets()
        return redirect(url_for('index'))

    return render_template('add_staff.html')

# Google Sheets Sync Functions
def sync_to_google_sheets(spreadsheet_id, range_name, data):
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)

    body = {
        'values': data
    }

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

def sync_products_to_google_sheets():
    try:
        products = fetch_products()
        if not products:
            print("No products found to sync.")
            return
        
        product_data = [['product_name', 'quantity', 'description', 'last_updated']] + [
            [p[0], p[1], p[2], p[3].strftime('%Y-%m-%d') if isinstance(p[3], date) else str(p[3])] for p in products
        ]
        
        sync_to_google_sheets(SPREADSHEET_ID_PRODUCTS, RANGE_NAME_PRODUCTS, product_data)
        print("Products synced successfully!")
    except Exception as e:
        print(f"An error occurred while syncing products: {e}")

def sync_users_to_google_sheets():
    try:
        users = fetch_users()
        if not users:
            print("No users found to sync.")
            return
        
        user_data = [['username', 'role']] + [
            [u[0], u[1]] for u in users
        ]
        
        sync_to_google_sheets(SPREADSHEET_ID_USERS, RANGE_NAME_USERS, user_data)
        print("Users synced successfully!")
    except Exception as e:
        print(f"An error occurred while syncing users: {e}")

def sync_staff_to_google_sheets():
    try:
        staff = fetch_staff()  # Fetch the staff data
        if not staff:
            print("No staff found to sync.")
            return
        
        staff_data = [['Staff ID', 'Username', 'Position', 'Salary']] + [
            [s[0], s[1], s[2], float(s[3])] for s in staff  # Convert salary to float
        ]

        sync_to_google_sheets(SPREADSHEET_ID_STAFF, RANGE_NAME_STAFF, staff_data)
        print("Staff synced successfully!")
    except Exception as e:
        print(f"An error occurred while syncing staff: {e}")

@app.route('/sync_from_google_sheets', methods=['GET'])
def sync_from_google_sheets():
    direction = request.args.get('direction')

    if direction == 'to_mysql':
        sync_to_mysql_users()  # Sync users first
        sync_to_mysql_products()
        sync_to_mysql_staff()  # Sync staff last
        flash('All data synced from Google Sheets to MySQL!', 'success')
    elif direction == 'to_google_sheets':
        sync_products_to_google_sheets()
        sync_users_to_google_sheets()
        sync_staff_to_google_sheets()
        flash('All data synced to Google Sheets!', 'success')
    else:
        flash('Invalid sync direction specified.', 'danger')

    return redirect(url_for('index'))



def fetch_from_google_sheets(spreadsheet_id, range_name):
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)

    # Call the Sheets API
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])

    return values

def fetch_products_from_google_sheets():
    data = fetch_from_google_sheets(SPREADSHEET_ID_PRODUCTS, RANGE_NAME_PRODUCTS)
    return data[1:]  # Skip header row

def fetch_users_from_google_sheets():
    data = fetch_from_google_sheets(SPREADSHEET_ID_USERS, RANGE_NAME_USERS)
    return data[1:]  # Skip header row

def fetch_staff_from_google_sheets():
    data = fetch_from_google_sheets(SPREADSHEET_ID_STAFF, RANGE_NAME_STAFF)
    return data[1:]  # Skip header row

def sync_to_mysql_products():
    products = fetch_products_from_google_sheets()
    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    # Clear existing products
    cursor.execute("DELETE FROM products")
    
    for product in products:
        product_name, quantity, description, last_updated = product
        cursor.execute("""
            INSERT INTO products (product_name, quantity, description, last_updated)
            VALUES (%s, %s, %s, %s)
        """, (product_name, int(quantity), description, last_updated))

    db_conn.commit()
    cursor.close()
    db_conn.close()

def sync_to_mysql_users():
    users = fetch_users_from_google_sheets()
    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    # Clear existing users
    cursor.execute("DELETE FROM users")
    
    for user in users:
        username, role = user
        cursor.execute("""
            INSERT INTO users (username, role) 
            VALUES (%s, %s)
        """, (username, role))

    db_conn.commit()
    cursor.close()
    db_conn.close()

def sync_to_mysql_staff():
    # Assume you fetch staff data from Google Sheets
    staff_data = fetch_staff_from_google_sheets()  # Ensure this returns a list of dictionaries

    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    for staff in staff_data:  # Iterate over the list
        if isinstance(staff, dict):  # Check if each staff entry is a dictionary
            user_id = staff.get('user_id')  # Use .get() for safe access
            
            # Check if user_id exists in the users table
            cursor.execute("SELECT COUNT(*) FROM users WHERE id = %s", (user_id,))
            exists = cursor.fetchone()[0]

            if exists:
                # Proceed with insert if user_id exists
                cursor.execute(""" 
                    INSERT INTO staff (user_id, other_columns) VALUES (%s, %s)
                """, (user_id, staff['other_data']))  # Adjust as necessary
            else:
                print(f"User ID {user_id} does not exist. Skipping staff entry.")
        else:
            print("Unexpected staff data format:", staff)

    db_conn.commit()
    cursor.close()
    db_conn.close()




if __name__ == '__main__':
    
    app.run(debug=True)
