import os
from flask import Flask, request, redirect, render_template, jsonify, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

app = Flask(__name__)

# Configure the database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

GROUP_SIZE = 5

# ---------- MODELS ---------- #

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    degree_id = db.Column(db.Integer, db.ForeignKey('degrees.id'), nullable=False)
    major_id = db.Column(db.Integer, db.ForeignKey('majors.id'), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    degree = db.relationship('Degree')
    major = db.relationship('Major')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Degree(db.Model):
    __tablename__ = 'degrees'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)

class Major(db.Model):
    __tablename__ = 'majors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    dept = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)

class BuddyRequest(db.Model):
    """A student waiting to be paired with a buddy for a shared course."""
    __tablename__ = 'buddy_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    status = db.Column(db.String(10), default='waiting')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student')
    course = db.relationship('Course')

class BuddyMatch(db.Model):
    """A confirmed 1:! buddy pairing for a shared course"""
    __tablename__ = 'buddy_matches'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_a_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student_b_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course')
    student_a = db.relationship('Student', foreign_keys=[student_a_id])
    student_b = db.relationship('Student', foreign_keys=[student_b_id])

class Group(db.Model):
    """A student group. Needs GROUP_SIZE to be at least 5 members"""
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    is_full = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    courses = db.relationship('Course')
    members = db.relationship('GroupMember', backref='group', lazy=True,
                              order_by='GroupMember.joined_at')
class GroupMember(db.Model):
    __tablename__ = 'group_members'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student')

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



# Creates all the tables for the database
with app.app_context():
    db.create_all()

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
            session['auth_event'] = 'logim'
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    student = current_student()
    matches = student_buddy_matches(student.id)
    groups = student_groups(student.id)
    pending_request = (BuddyRequest.query
                       .filter_by(student_id=student.id, status='waiting')
                       .first())
    auth_event = session.pop('auth_event', None)
    return render_template('dashboard.html',
                           student=student,
                           matches=matches,
                           groups=groups,
                           pending_request=pending_request,
                           auth_event=auth_event)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# student_id is  
# all_courses
@app.route('/find_buddies', methods=['GET', 'POST'])
def find_buddies():

    #Grabs the student id from the session
    student_id = session.get('student_id')

    if not student_id:
        return redirect(url_for('login'))
    
    current_student = Student.query.get_or_404(student_id) # Saves the current student while they are logged in

    # Queries all the courses for a student to select to find buddies for that course
    all_courses = Course.query.order_by(Course.dept).all()
    buddies = []
    selected_course = None

    # Handles the form submission for finding buddies
    if request.method == 'POST':
        dept = request.form.get('dept')
        code = request.form.get('code')
        name = request.form.get('name')

        selected_course = Course.query.filter_by(dept=dept, code=code, name=name).first() # Finds the selected course from the database based on the form input

        # If the selected course exists, query the buddies for that course
        if selected_course:
            buddies = Buddy.query.filter_by(course_id=selected_course.id).all()
        else:
            jsonify({'message': 'Course not found', 'status': 'error'})

    return render_template('find_buddies.html', current_student=current_student, all_courses=all_courses, buddies=buddies, selected_course=selected_course)

@app.route('/find_groups')
def find_groups():    
    return render_template('find_groups.html')


if __name__ == '__main__':
    app.debug = True
    ip = '127.0.0.1'
    app.run(host=ip)