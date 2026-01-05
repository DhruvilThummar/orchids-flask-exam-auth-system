from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Needed for session management

# --- DATABASE SETUP ---
def init_db():
    # Connect to SQLite database (creates database.db if it doesn't exist)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Create the 'users' table based on the strict requirements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

# --- ROUTES ---

@app.route('/')
def index():
    # Redirect to login page by default
    return redirect(url_for('login'))

# 1. User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get data from form fields
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        # Simple password hashing
        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            # Insert new user into the database
            cursor.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)', 
                           (name, email, hashed_password, role))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            # Handle unique email constraint error
            flash('Email already exists. Please use a different one.', 'danger')
            return redirect(url_for('register'))
            
    return render_template('register.html')

# 2. User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        # Find user by email
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        # Check if user exists and password is correct
        if user and check_password_hash(user[3], password):
            # Save user info in session
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_role'] = user[4]
            
            # Redirect based on role
            if user[4] == 'Student':
                return redirect(url_for('student_dashboard'))
            elif user[4] == 'Teacher':
                return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('login.html')

# 3. Student Dashboard
@app.route('/student/dashboard')
def student_dashboard():
    # Prevent unauthorized access
    if 'user_id' not in session or session['user_role'] != 'Student':
        flash('Please login as a student to access this page.', 'danger')
        return redirect(url_for('login'))
    return render_template('student_dashboard.html', name=session['user_name'], role=session['user_role'])

# 4. Teacher Dashboard
@app.route('/teacher/dashboard')
def teacher_dashboard():
    # Prevent unauthorized access
    if 'user_id' not in session or session['user_role'] != 'Teacher':
        flash('Please login as a teacher to access this page.', 'danger')
        return redirect(url_for('login'))
    return render_template('teacher_dashboard.html', name=session['user_name'], role=session['user_role'])

# 5. Logout
@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)
