import os
from flask import Flask, request, redirect, render_template, jsonify, session, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure the database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#Student model
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    degree_id = db.Column(db.Integer, db.ForeignKey('degrees.id'), nullable=False)
    major_id = db.Column(db.Integer, db.ForeignKey('majors.id'), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

#Degree model
class Degree(db.Model):
    __tablename__ = 'degrees'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)

    students = db.relationship('Student', backref='degree', lazy=True)

#Major model
class Major(db.Model):
    __tablename__ = 'majors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    students = db.relationship('Student', backref='major', lazy=True)

# Creates all the tables for the database
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    
    #Queries all degrees
    all_degrees = Degree.query.all()
    #Queries all majors
    all_majors = Major.query.all()

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        degree_id = request.form.get('degree_id')
        major_id = request.form.get('major_id')
        username = request.form.get('degree_id')
        password = request.form.get('password')
        
    # Checks if the username exists
        existing_student = Student.query.filter_by(username=username).first()
        if existing_student:
            return jsonify({'message': 'Username exists...', 'status': 'error'})
    
        #Adds the new student to the database
        new_student = Student(first_name=first_name,
                          last_name=last_name,
                          degree_id=degree_id,
                          major_id=major_id,
                          username=username,
                          password=password)
    
        db.session.add(new_student)
        db.session.commit()
    
        session['first_name'] = first_name
        session['new_student'] = True
        
        return jsonify({'status': 'success'})

    return render_template('register.html', all_degrees=all_degrees, all_majors=all_majors)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        student = Student.query.filter_by(username=username).first()

        if student and student.passowrd == password:
            session['first_name'] = student.first_name
            session['new_student'] = False
            return jsonify({'status': 'success'})
        
        return jsonify({'message':'Sorry, the username or password is unavilable', 'status':'error'})
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():

    # If the first name of a student is not in the dashboard, redirect to login
    if 'first_name' not in session:
        return redirect(url_for('login'))
    
    first_name = session['first_name']
    new_student = session.get('new_student', None)

    if new_student == True:
        message = f'Welcome to your dashboard, {first_name}!'
    elif new_student == False:
        message = f'Welcome back, {first_name}!'
    else:
        message = f"{first_name}'s dashboard"
    
    return render_template('dashboard.html', message=message, first_name=first_name)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.debug = True
    ip = '127.0.0.1'
    app.run(host=ip)