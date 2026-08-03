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

GROUP_SIZE = 4

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

# student_id is  
# all_courses
@app.route('/find_buddies', methods=['GET', 'POST'])
def find_buddies():
    return render_template('find_buddies.html')

@app.route('/find_groups')
def find_groups():    
    return render_template('find_groups.html')


# ----------  Delete Your Buddy from the Dashboard ---------- #
@app.route('/buddy/<int:match_id>/end', methods=['POST'])
@login_required
def delete_buddy(match_id):
    student = current_student()
    match = db.session.get(BuddyMatch, match_id)
    if match and student.id in (match.student_a_id, match.student_b_id):
        db.session.delete(match)
        db.session.commit()
    return redirect(url_for('dashboard'))

# ---------- Leave Your Group from the Dashboard ---------- #
@app.route('/group/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    student = current_student()
    group_member = GroupMember.query.filter_by(group_id=group_id, student_id=student.id).first()
    if group_member:
        group = db.session.get(Group, group_id)
        db.session.delete(group_member)
        # Check if the group is now empty
        if group and group.is_full:
            group.is_full = False
        db.session.commit()
    return redirect(url_for('dashboard'))

# ---------- Seed Example Data ---------- #
def seed_students():
    if Student.query.count() == 0:
        return

    def student(first_name, last_name, degree_type, major_name, username):
        degree = Degree.query.filter_by(type=degree_type).first()
        major = Major.query.filter_by(name=major_name).first()
        s = Student(first_name=first_name, last_name=last_name,
                    degree_id=degree.id, major_id=major.id,
                    username=username)
        s.set_password('studybuddy123')
        db.session.add(s)
        db.session.flush()
        return s

    noah_sweatte = student(first_name='Noah', last_name='Sweatte', degree_id=1, major_id=1, username='noah_sweatte')
    mason_hoggard = student(first_name='Mason', last_name='Hoggard', degree_id=1, major_id=1, username='mason_hoggard')
    john_hills = student(first_name='John', last_name='Hills', degree_id=2, major_id=2, username='john_hills')
    andrew_smith = student(first_name='Andrew', last_name='Smith', degree_id=2, major_id=2, username='andrew_smith')
    edward_hendron = student(first_name='Edward', last_name='Hendron', degree_id=1, major_id=3, username='edward_hendron')

    mia_jones = student(first_name='Mia', last_name='Jones', degree_id=1, major_id=3, username='mia_ding')
    emma_jones = student(first_name='Emma', last_name='Jones', degree_id=2, major_id=4, username="emma_jones")
    haley_wells =  student(first_name='Haley', last_name='Wells', degree_id=2, major_id=4, username="haley_wells")
    samantha_baker = student(first_name='Samantha', last_name='Baker', degree_id=1, major_id=5, username="samantha_baker")
    josie_andrews = student(first_name='Josie', last_name='Andrews', degree_id=1, major_id=5, username="josie_andrews")

    db.session.commit()

    def searching_buddy(student_row, course_dept, course_code):
        course = Course.query.filter_by(dept=course_dept, code=course_code).first()
        db.session.add(BuddyRequest(student_id=student_row.id, course_id=course.id))

    searching_buddy(noah_sweatte, 'CSCI', '1010')
    searching_buddy(mason_hoggard, 'CSCI', '1010')
    searching_buddy(john_hills, 'MATH', '2121')
    searching_buddy(josie_andrews, 'COMM', '2020')

    def searching_group(course_dept, course_code, members):
        course = Course.query.filter_by(dept=course_dept, code=course_code).first()
        group = Group(course_id=course.id)
        db.session.add(group)
        db.session.flush()  # Flush to get the group ID
        for member in members:
            db.session.add(GroupMember(group_id=group.id, student_id=member.id))

    searching_group('CSCI', '2400', [mia_jones, emma_jones, haley_wells])
    searching_group('MATH', '2228', [edward_hendron, andrew_smith, samantha_baker])

with app.app_context():
    db.create_all()
    seed_students()

if __name__ == '__main__':
    app.debug = True
    ip = '127.0.0.1'
    app.run(host=ip)