import os
from flask import Flask, request, redirect, render_template, jsonify, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

load_dotenv()

app = Flask(__name__)

# Configure the database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///study_buddy.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

GROUP_SIZE = 5

# ---------- MODELS ---------- #

# Degree Model
class Degree(db.Model):
    __tablename__ = 'degree'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)

# Major Model
class Major(db.Model):
    __tablename__ = 'major'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

# Course Model
class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)

# Student Model
class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    degree_id = db.Column(db.Integer, db.ForeignKey('degree.id'), nullable=False)
    major_id = db.Column(db.Integer, db.ForeignKey('major.id'), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    degree = db.relationship('Degree')
    major = db.relationship('Major')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Buddy Request Model
class BuddyRequest(db.Model):
    __tablename__ = 'buddy_request'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    status = db.Column(db.String(10), default='waiting')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student')
    course = db.relationship('Course')

# Buddy Match Model
class BuddyMatch(db.Model):
    """ A confirmed 1:1 buddy pairing for a course. """
    __tablename__ = 'buddy_match'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    student_a_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    student_b_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course')
    student_a = db.relationship('Student', foreign_keys=[student_a_id])
    student_b = db.relationship('Student', foreign_keys=[student_b_id])

# Group Model
# Example: Whenever a student select a course [course.id]
# Groups to join
class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    is_full = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course')
    members = db.relationship('GroupMember', backref='group', lazy=True)

    # what does that mean?
    # 
    @property
    def member_count(self):
        return len(self.members)

# Group Member Model
class GroupMember(db.Model):
    __tablename__ = 'group_member'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)

# ----------- Auth Helpers ----------#
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'student_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def current_student():
    if 'student_id' in session:
        return db.session.get(Student, session['student_id'])
    return None

def student_buddy_matches(student_id):
    return (BuddyMatch.query
            .filter(db.or_(BuddyMatch.student_a_id == student_id,
                            BuddyMatch.student_b_id == student_id))
            .order_by(BuddyMatch.created_at.desc())
            .all())

def student_groups(student_id):
    return (Group.query
            .join(GroupMember)
            .filter(GroupMember.student_id == student_id)
            .order_by(Group.created_at.desc())
            .all())  

# ---------- Auth Routes ----------

@app.route('/')
def index():
    if current_student():
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    all_degrees = Degree.query.order_by(Degree.type).all()
    all_majors = Major.query.order_by(Major.name).all()

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        degree_id = request.form.get('degree_id')
        major_id = request.form.get('major_id')
        username = request.form.get('username')
        password = request.form.get('password')

        # Checks to see if all needs to be required
        if not all([first_name, last_name, degree_id, major_id, username, password]):
            return render_template('register.html', all_degrees=all_degrees,
                                   all_majors=all_majors,
                                   error="All fields are required.")
        
        # Checks if the username exists
        if Student.query.filter_by(username=username).first():
            return render_template('register.html', all_degrees=all_degrees,
                                   all_majors=all_majors,
                                   error="Username already existed.")
    
        #Adds the new student to the database
        student = Student(first_name=first_name,
                          last_name=last_name,
                          degree_id=degree_id,
                          major_id=major_id,
                          username=username)
        student.set_password(password)
        db.session.add(student)
        db.session.commit()
        session['student_id'] = student.id
        session['auth_event'] = 'register'
        return redirect(url_for('dashboard'))

    return render_template('register.html', 
                           all_degrees=all_degrees, 
                           all_majors=all_majors)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        student = Student.query.filter_by(username=username).first()
        if student and student.check_password(password):
            session['student_id'] = student.id
            session['auth_event'] = 'login'
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    student = current_student()
    matches = student_buddy_matches(student.id)
    groups = student_groups(student.id)
    auth_event = session.pop('auth_event', None)
    return render_template('dashboard.html',
                           student=student,
                           matches=matches,
                           groups=groups,
                           auth_event=auth_event)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------- Course Picker ---------- #

def course_subjects():
    return db.session.scalars(
        db.select(Course.department).distinct().order_by(Course.department)
    ).all()

@app.route('/course.json')
@login_required
def course_json():
    subject = request.args.get('subject') or request.args.get('department', '')
    if not subject:
        return jsonify([])
    courses = Course.query.filter_by(department=subject).order_by(Course.code).all()
    return jsonify([{'id': course.id, 'code': course.code, 'name': course.name} for course in courses])

# ---------- Finding a Group ---------- #
@app.route('/find_groups')
@login_required
def find_groups():
    return render_template('find_groups.html')

# ---------- Finding a Buddy ---------- #
@app.route('/find_buddies', methods=['GET', 'POST'])
@login_required
def find_buddies():
    subjects = course_subjects()
    error = request.args.get('error')
    candidates = None

    if request.method == 'POST':
        course_id = request.form.get('course_id', type=int)
        if not course_id:
            error = 'Please select a course...'
        else:
            student = current_student()
            waiting = (BuddyRequest.query
                       .filter_by(course_id=course_id, status='waiting')
                       .filter(BuddyRequest.student_id != student.id)
                       .order_by(BuddyRequest.created_at.asc())
                       .all())
            candidates = []
            for buddies in waiting:
                candidates.append({'request_id': buddies.id,
                                   'first_name': buddies.student.first_name,
                                   'last_name': buddies.student.last_name})

    return render_template('find_buddies.html', subjects=subjects,
                           candidates=candidates, error=error)

# Matches with the current student who is taking the same course
@app.route('/buddy-request/<int:request_id>/match', methods=['POST'])
@login_required
def match_buddy_request(request_id):
    student = current_student()
    waiting = db.session.get(BuddyRequest, request_id)
    if not waiting or waiting.status != 'waiting':
        return redirect(url_for('find_buddies', error='That student is not takimg the course'))
    if waiting.student_id == student.id:
        return redirect(url_for('find_buddies'), error='You cannot match with yourself...')
    course = waiting.course

    already_matched = BuddyMatch.query.filter(
        db.or_(BuddyMatch.student_a_id == student.id, BuddyMatch.student_b_id == student.id),
        BuddyMatch.course_id == waiting.course_id
    ).first()
    
    if already_matched:
        return redirect(url_for('find_buddies'), error='You already matched this student!')

    waiting.status = 'matched'
    db.session.add(BuddyMatch(course_id = waiting.course_id, student_a_id=student.id,
                              student_b_id=waiting.student_id))
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/find-buddy/cancel', methods=['POST'])
@login_required
def cancel_buddy_request():
    student = current_student()
    request = BuddyRequest.query.filter_by(student_id=student.id, status='waiting').first()
    if request:
        db.session.delete(request)
        db.session.commit()
    return redirect(url_for('dashboard'))

# ---------- Seed Example Data ---------- #

def seed_degrees():
    if Degree.query.first():
        return
    types = ['Bachelor of Arts', 'Bachelor of Science']
    for type in types:
        db.session.add(Degree(type=type))
    db.session.commit()

def seed_majors():
    if Major.query.first():
        return
    names = ['Computer Science', 'Accounting', 'Software Engineering', 'Information Technology', 'Information and Cybersecurity Technology']
    for name in names:
        db.session.add(Major(name=name))
    db.session.commit()

def seed_courses():
    if Course.query.first():
        return
    courses = [
        ('CSCI', '1010', 'Algortihm Problem Solving'),
        ('CSCI', '2400', 'Discrete Structures I'),
        ('CSCI', '3675', 'Principles of Programming Languages'),
        ('CSCI', '4602', 'Automata, Computability and Complexity'),
        ('MATH', '2121', 'Calculus for Life Sciences'),
        ('MATH', '2228', 'Elementary Statistics'),
        ('GEOL', '1500', 'Dynamic Earth'),
        ('COMM', '2020', 'Fundamentals of Communication Speech'),
    ]
    for department, code, name in courses:
        db.session.add(Course(department=department, code=code, name=name))
    db.session.commit()

def seed_students():
    def student(first_name, last_name, degree_type, major_name, username):
        existing = Student.query.filter_by(username=username).first()
        if existing:
            return existing
        degree = Degree.query.filter_by(type=degree_type).first()
        major = Major.query.filter_by(name=major_name).first()
        s = Student(first_name=first_name, 
                    last_name=last_name,
                    degree_id=degree.id, 
                    major_id=major.id,
                    username=username)
        s.set_password('buddy123')
        db.session.add(s)
        db.session.flush()
        return s

    noah_sweatte = student('Noah', 'Sweatte', 'Bachelor of Science', 'Software Engineering', 'noah_sweatte')
    mason_hoggard = student('Mason', 'Hoggard', 'Bachelor of Arts', 'Information Technology', 'mason_hoggard')
    josie_andrews = student('Josie', 'Andrews', 'Bachelor of Science', 'Accounting', 'josie_andrews')

    db.session.commit()

    def searching_buddy(student_row, department, code):
        course = Course.query.filter_by(department=department, code=code).first()
        if not course:
            return
        db.session.add(BuddyRequest(student_id=student_row.id, course_id=course.id))

    searching_buddy(noah_sweatte, 'CSCI', '1010')
    searching_buddy(mason_hoggard, 'CSCI', '2400')
    searching_buddy(josie_andrews, 'COMM', '2020')

with app.app_context():
    db.create_all()
    seed_degrees()
    seed_majors()
    seed_courses()
    seed_students()

if __name__ == '__main__':
    app.debug = True
    ip = '127.0.0.1'
    app.run(host=ip)