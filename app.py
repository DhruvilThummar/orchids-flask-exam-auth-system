from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import datetime
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
    
    # Module 2: Exams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            total_marks INTEGER,
            duration INTEGER,
            max_tab_switches INTEGER,
            created_by INTEGER
        )
    ''')

    # Module 3: Questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            question_text TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_option TEXT
        )
    ''')

    # Module 3: Student Answers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            exam_id INTEGER,
            question_id INTEGER,
            selected_option TEXT
        )
    ''')

    # Module 4: Violations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            exam_id INTEGER,
            violation_count INTEGER,
            last_violation_time TEXT
        )
    ''')

    # Seed some sample data for Module 3 testing if empty
    cursor.execute('SELECT COUNT(*) FROM exams')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO exams (title, description, total_marks, duration, max_tab_switches, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("Python Basics", "A simple exam on Python fundamentals.", 20, 10, 3, 1))
        exam_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO questions (exam_id, question_text, option_a, option_b, option_c, option_d, correct_option)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (exam_id, "What is the output of print(2**3)?", "6", "8", "9", "12", "B"))
        cursor.execute('''
            INSERT INTO questions (exam_id, question_text, option_a, option_b, option_c, option_d, correct_option)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (exam_id, "Which of these is a mutable data type in Python?", "Tuple", "String", "List", "Integer", "C"))
    
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
    
    # Fetch all available exams
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM exams')
    exams = cursor.fetchall()
    conn.close()
    
    return render_template('student_dashboard.html', 
                           name=session['user_name'], 
                           role=session['user_role'],
                           exams=exams)

# 4. Teacher Dashboard
@app.route('/teacher/dashboard')
def teacher_dashboard():
    # Prevent unauthorized access
    if 'user_id' not in session or session['user_role'] != 'Teacher':
        flash('Please login as a teacher to access this page.', 'danger')
        return redirect(url_for('login'))
    
    # Fetch exams created by this teacher
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM exams WHERE created_by = ?', (session['user_id'],))
    my_exams = cursor.fetchall()
    conn.close()
    
    return render_template('teacher_dashboard.html', 
                           name=session['user_name'], 
                           role=session['user_role'],
                           exams=my_exams)

# --- MODULE 2: EXAM CREATION ---
@app.route('/teacher/create_exam', methods=['GET', 'POST'])
def create_exam():
    # Role Check
    if 'user_id' not in session or session['user_role'] != 'Teacher':
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        total_marks = int(request.form['total_marks'])
        duration = int(request.form['duration'])
        max_tab_switches = int(request.form['max_tab_switches'])
        teacher_id = session['user_id']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO exams (title, description, total_marks, duration, max_tab_switches, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, total_marks, duration, max_tab_switches, teacher_id))
        conn.commit()
        conn.close()
        
        flash('Exam created successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    return render_template('create_exam.html')

# --- MODULE 3: EXAM ATTEMPT ---
@app.route('/student/attempt_exam/<int:exam_id>')
def attempt_exam(exam_id):
    # Role Check
    if 'user_id' not in session or session['user_role'] != 'Student':
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get exam details
    cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
    exam = cursor.fetchone()
    
    if not exam:
        flash('Exam not found', 'danger')
        return redirect(url_for('student_dashboard'))

    # Get questions
    cursor.execute('SELECT * FROM questions WHERE exam_id = ?', (exam_id,))
    questions = cursor.fetchall()
    
    conn.close()
    
    return render_template('attempt_exam.html', exam=exam, questions=questions)

@app.route('/student/submit_exam/<int:exam_id>', methods=['POST'])
def submit_exam(exam_id):
    if 'user_id' not in session or session['user_role'] != 'Student':
        return redirect(url_for('login'))

    student_id = session['user_id']
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get all questions for this exam to calculate score
    cursor.execute('SELECT id, correct_option FROM questions WHERE exam_id = ?', (exam_id,))
    questions = cursor.fetchall()
    
    score = 0
    total_questions = len(questions)
    
    # Save answers and calculate score
    for q_id, correct_opt in questions:
        selected_opt = request.form.get(f'question_{q_id}')
        
        # Save to database
        cursor.execute('''
            INSERT INTO student_answers (student_id, exam_id, question_id, selected_option)
            VALUES (?, ?, ?, ?)
        ''', (student_id, exam_id, q_id, selected_opt))
        
        if selected_opt == correct_opt:
            score += 1

    # Calculate marks obtained (based on total_marks from exam table)
    cursor.execute('SELECT total_marks FROM exams WHERE id = ?', (exam_id,))
    exam_total_marks = cursor.fetchone()[0]
    
    marks_obtained = (score / total_questions * exam_total_marks) if total_questions > 0 else 0
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('exam_result', exam_id=exam_id, marks=marks_obtained, total=exam_total_marks))

@app.route('/student/exam_result')
def exam_result():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    exam_id = request.args.get('exam_id')
    marks = request.args.get('marks')
    total = request.args.get('total')
    
    return render_template('exam_result.html', marks=marks, total=total)

# --- MODULE 4: ANTI-CHEATING ---
@app.route('/student/log_violation', methods=['POST'])
def log_violation():
    if 'user_id' not in session or session['user_role'] != 'Student':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.json
    exam_id = data.get('exam_id')
    student_id = session['user_id']
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Check if violation record exists
    cursor.execute('SELECT violation_count FROM violations WHERE student_id = ? AND exam_id = ?', 
                   (student_id, exam_id))
    record = cursor.fetchone()
    
    if record:
        new_count = record[0] + 1
        cursor.execute('UPDATE violations SET violation_count = ?, last_violation_time = ? WHERE student_id = ? AND exam_id = ?',
                       (new_count, current_time, student_id, exam_id))
    else:
        new_count = 1
        cursor.execute('INSERT INTO violations (student_id, exam_id, violation_count, last_violation_time) VALUES (?, ?, ?, ?)',
                       (student_id, exam_id, new_count, current_time))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'count': new_count})

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
