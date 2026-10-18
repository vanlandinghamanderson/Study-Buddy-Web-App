#!/usr/bin/env python
"""Initialize the database with seed data."""

from main import app, db, Degree, Major, Course, Student, BuddyRequest, Group, GroupMember, GROUP_SIZE

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
    courses = [
        ('CSCI', '1010', 'Algortihm Problem Solving'),
        ('CSCI', '2400', 'Discrete Structures I'),
        ('CSCI', '3675', 'Principles of Programming Languages'),
        ('CSCI', '4602', 'Automata, Computability and Complexity'),
        ('MATH', '2121', 'Calculus for Life Sciences'),
        ('MATH', '2228', 'Elementary Statistics'),
        ('GEOL', '1500', 'Dynamic Earth'),
        ('COMM', '2020', 'Fundamentals of Communication Speech'),
        ('PHIL', '2275', 'Professional Ethics'),
    ]
    for department, code, name in courses:
        existing = Course.query.filter_by(department=department, code=code).first()
        if existing:
            continue
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

    antonino_baker = student('Antonio', 'Baker', 'Bachelor of Science', 'Computer Science', 'antonio_baker')
    sue_anderson = student('Sue', 'Anderson', 'Bachelor of Science', 'Information and Cybersecurity Technology', 'sue_anderson')

    def searching_buddy(student_row, department, code):
        course = Course.query.filter_by(department=department, code=code).first()
        if not course:
            return
        if BuddyRequest.query.filter_by(student_id=student_row.id, course_id=course.id).first():
            return
        db.session.add(BuddyRequest(student_id=student_row.id, course_id=course.id))

    searching_buddy(noah_sweatte, 'CSCI', '1010')
    searching_buddy(mason_hoggard, 'CSCI', '1010')
    searching_buddy(josie_andrews, 'COMM', '2020')
    db.session.commit()

    def groups(department, code, members):
        course = Course.query.filter_by(department=department, code=code).first()
        if not course:
            return
        existing_group = Group.query.filter_by(course_id=course.id).first()
        if existing_group:
            return
        group = Group(course_id=course.id)
        db.session.add(group)
        db.session.flush()
        for member in members:
            if not GroupMember.query.filter_by(group_id=group.id, student_id=member.id).first():
                db.session.add(GroupMember(group_id=group.id, student_id=member.id))
        # Mark group as full if it has GROUP_SIZE members
        if len(members) >= GROUP_SIZE:
            group.is_full = True
        db.session.commit()

    groups('CSCI', '4602', [antonino_baker, sue_anderson])
    groups('PHIL', '2275', [noah_sweatte, mason_hoggard, antonino_baker, josie_andrews])

    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("Seeding database...")
        seed_degrees()
        print("✓ Degrees seeded")
        seed_majors()
        print("✓ Majors seeded")
        seed_courses()
        print("✓ Courses seeded")
        seed_students()
        print("✓ Students and groups seeded")
        print("Database initialized successfully!")
