from flask import Flask, render_template, request, redirect, flash
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = 'secret123'

INVALID_NAMES = ['google']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "database", "contacts.db")

def get_db():
    return sqlite3.connect(DB)

# 🟢 Create DB
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        address TEXT,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

init_db()

# 🟢 Email validation
def is_valid_email(email):
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return bool(re.match(pattern, email))

# 🟢 Phone validation
def is_valid_phone(phone):
    return phone.isdigit() and len(phone) == 10


# 🟢 Home page
@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts")
    contacts = cursor.fetchall()
    conn.close()
    return render_template('index.html', contacts=contacts)


# 🟢 ADD CONTACT
@app.route('/add', methods=['GET', 'POST'])
def add_contact():
    if request.method == 'POST':

        # 🔥 IMPORTANT: lowercase for validation
        first_name = request.form['first_name'].strip().lower()
        last_name = request.form['last_name'].strip().title()
        address = request.form['address'].strip().title()
        email = request.form['email'].strip().lower()
        phone = request.form['phone'].strip()

        if not first_name or not last_name or not email or not phone:
            flash("All required fields must be filled!")
            return redirect('/add')
        
        if first_name in INVALID_NAMES:
            flash("Google is not a valid first name")
            return redirect('/add')

        if not is_valid_email(email):
            flash("Invalid email format!")
            return redirect('/add')

        if not is_valid_phone(phone):
            flash("Phone must be 10 digits!")
            return redirect('/add')

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM contacts WHERE email=?", (email,))
        if cursor.fetchone():
            conn.close()
            flash("Email already exists!")
            return redirect('/add')

        # ✅ Insert data
        cursor.execute("""
        INSERT INTO contacts (first_name, last_name, address, email, phone)
        VALUES (?, ?, ?, ?, ?)
        """, (first_name, last_name, address, email, phone))

        conn.commit()
        conn.close()

        flash("Contact added successfully!")
        return redirect('/')

    return render_template('add_contact.html')


# 🟢 EDIT CONTACT
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_contact(id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        first_name = request.form['first_name'].strip().lower()
        last_name = request.form['last_name'].strip().title()
        address = request.form['address'].strip().title()
        email = request.form['email'].strip().lower()
        phone = request.form['phone'].strip()

        error = None

        if not first_name or not last_name or not email or not phone:
            error = "All fields required!"
        elif not is_valid_email(email):
            error = "Invalid email!"
        elif not is_valid_phone(phone):
            error = "Invalid phone!"
        elif first_name in INVALID_NAMES:
            error = "Invalid first name!"

        cursor.execute("SELECT * FROM contacts WHERE email=? AND id!=?", (email, id))
        if cursor.fetchone():
            error = "Email already exists!"

        if error:
            cursor.execute("SELECT * FROM contacts WHERE id=?", (id,))
            contact = cursor.fetchone()
            conn.close()
            return render_template('edit_contact.html', contact=contact, error=error)

        cursor.execute("""
        UPDATE contacts
        SET first_name=?, last_name=?, address=?, email=?, phone=?
        WHERE id=?
        """, (first_name, last_name, address, email, phone, id))

        conn.commit()
        conn.close()

        return redirect('/')

    cursor.execute("SELECT * FROM contacts WHERE id=?", (id,))
    contact = cursor.fetchone()
    conn.close()

    return render_template('edit_contact.html', contact=contact)


# 🟢 DELETE
@app.route('/delete/<int:id>')
def delete_contact(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contacts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)