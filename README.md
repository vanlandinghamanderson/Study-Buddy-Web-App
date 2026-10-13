S
Readme · MD
# Study Buddy
 
A Flask web app that helps college students find study partners and study groups for the courses they're taking. Students sign up, pick a course, and either match one-on-one with a classmate or join a small study group. Everything they've joined appears on their dashboard.
 
Built as a Web Applications project at East Carolina University.
 
## The problem
 
Finding someone to study with usually depends on who you happen to sit next to. Study Buddy makes it a quick search: choose your course and see which classmates are also looking for help, or which groups still have open seats.
 
## Features
 
- **Accounts.** Students register with their name, degree, and major, then log in with a username and password. Passwords are hashed with Werkzeug, and pages that need an account redirect to the login screen.
- **Course picker.** Students choose a department, then a course code and name. The course lists load from a small JSON endpoint (`/course.json`) using jQuery AJAX, so there's no page reload between steps.
- **One-on-one buddy matching.** For a chosen course, the app lists classmates waiting for a buddy, oldest request first. Matching with one creates a confirmed pair. The app blocks matching with yourself and duplicate matches.
- **Study groups.** Students can browse open groups for a course (showing who's already in each one), join a group, or start a new one. Groups hold up to five students and close automatically when full. A student can only be in one group per course.
- **Dashboard.** Shows the student's buddy matches and groups in collapsible sections. Removing a match or leaving a group asks for confirmation in a pop-up first.
- **Sample data.** On first run, the app adds degrees, majors, nine real course listings, and demo students so it can be tried right away.
## Tech stack
 
| Layer | Tools |
| --- | --- |
| Backend | Python, Flask, Flask-SQLAlchemy |
| Database | PostgreSQL (falls back to SQLite for quick local runs) |
| Frontend | Jinja templates, HTML, CSS, jQuery, Bootstrap 4 |
| Auth | Flask sessions, Werkzeug password hashing |
| Config | `python-dotenv` |
 
## How matching works
 
```
Student picks a course
        │
        ├── Find a buddy ──► sees classmates waiting for that course ──► Match ──► BuddyMatch saved
        │
        └── Find a group ──► sees open groups (under 5 members) ──► Join ──► group marked full at 5
                         └─► no fit? Form a new group and become its first member
```
 
## Data model
 
| Table | Purpose |
| --- | --- |
| `student` | Account, name, degree, and major |
| `degree`, `major` | Lookup lists used at registration |
| `course` | Department, course code, and course name |
| `buddy_request` | A student waiting for a buddy in a course |
| `buddy_match` | A confirmed one-on-one pairing for a course |
| `group`, `group_member` | Study groups for a course and who's in them |
 
## Getting started
 
**Requirements:** Python 3.10+ (PostgreSQL optional).
 
1. Clone the repository:
```bash
   git clone https://github.com/vanlandinghamanderson/Study-Buddy-Web-App.git
   cd Study-Buddy-Web-App
```
 
2. Create and activate a virtual environment:
```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
```
 
3. Install dependencies:
```bash
   pip install flask flask-sqlalchemy python-dotenv psycopg2-binary
```
 
4. *(Optional)* To use PostgreSQL, create a `.env` file in the project root:
```
   DATABASE_URL=postgresql://your-user:your-password@localhost:5432/study_buddy
   SECRET_KEY=your-secret-key
```
 
   Without it, the app creates a local SQLite database (`study_buddy.db`).
 
5. Run the app:
```bash
   python main.py
```
 
   Open http://127.0.0.1:5000. Tables and sample data are created automatically on first run.
 
## Try it with demo accounts
 
Log in as any seeded student, such as **`taylor_wells`**, with the password **`buddy123`**. Then try finding a buddy for **CSCI 1010**, where two other students are already waiting, or joining the open group for **CSCI 4602**.
 
## Roadmap
 
- Let students send a buddy request when no one is waiting yet
- Add messaging or contact sharing between matched students
- Add a `requirements.txt` and automated tests
- Deploy a live demo

## Author
 
**Anderson Vanlandingham** — Computer Science, East Carolina University
[GitHub](https://github.com/vanlandinghamanderson)
