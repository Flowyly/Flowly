# ==============================
# IMPORT LIBRARIES
# ==============================
import email

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq
from dotenv import load_dotenv
import fitz
import traceback
import os


# ==============================
# CREATE FLASK APP
# ==============================
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# ==============================
# SQLITE CONFIGURATION
# ==============================
basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv(dotenv_path=os.path.join(basedir, ".env"))

print("DATABASE PATH:", os.path.join(basedir, "database.db"))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==============================
# GROQ CONFIG
# ==============================
api_key = os.getenv("GROQ_API_KEY", "").strip()

print("GROQ KEY LOADED:", api_key != "")

if not api_key:
    print("WARNING: GROQ_API_KEY not found in .env")

client = Groq(api_key=api_key)


# ==============================
# EMAIL CONFIGURATION
# ==============================
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    print("WARNING: Email credentials missing")


# ==============================
# DATABASE MODELS
# ==============================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Integer, default=0)


class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    topic = db.Column(db.String(200))
    content = db.Column(db.Text)
    created_by = db.Column(db.String(100))  # email of the user who generated this note
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)  # raw AI text, kept for the admin panel
    created_by = db.Column(db.String(100))  # email of the user who generated this quiz
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    marks = db.Column(db.String(20), default="0/0")
    attempted = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, nullable=True)


class Coursework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(50), default="Pending")

    created_by = db.Column(db.String(100))

# ==============================
# CREATE DATABASE TABLES
# ==============================
with app.app_context():
    db.create_all()


# ==============================
# HOME ROUTE
# ==============================
@app.route("/")
def home():
    return "Flowly Backend with Proper SQLite Running 🚀"


# ==============================
# ADMIN - GET ALL USERS
# ==============================
@app.route("/admin/users", methods=["GET"])
def admin_get_users():
    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "password": u.password,
            "is_admin": u.is_admin
        }
        for u in users
    ]), 200


# ==============================
# ADMIN - DELETE USER
# ==============================
@app.route("/admin/delete_user/<int:id>", methods=["DELETE"])
def admin_delete_user(id):
    user = User.query.get(id)

    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"success": True, "message": "User deleted"}), 200


# ==============================
# ADMIN - DELETE NOTE
# ==============================
@app.route("/admin/delete_note/<int:id>", methods=["DELETE"])
def admin_delete_note(id):
    note = Notes.query.get(id)

    if not note:
        return jsonify({"success": False, "message": "Note not found"}), 404

    db.session.delete(note)
    db.session.commit()

    return jsonify({"success": True, "message": "Note deleted"}), 200


# ==============================
# ADMIN - DELETE QUIZ
# ==============================
@app.route("/admin/delete_quiz/<int:id>", methods=["DELETE"])
def admin_delete_quiz(id):
    quiz = Quiz.query.get(id)

    if not quiz:
        return jsonify({"success": False, "message": "Quiz not found"}), 404

    db.session.delete(quiz)
    db.session.commit()

    return jsonify({"success": True, "message": "Quiz deleted"}), 200


# ==============================
# REGISTER ROUTE
# ==============================
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data sent"
            }), 400

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return jsonify({
                "success": False,
                "message": "Missing fields"
            }), 400

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return jsonify({
                "success": False,
                "message": "Email already exists"
            }), 400

        new_user = User(
            username=username,
            email=email,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Registration successful"
        }), 200

    except Exception as e:
        print("REGISTER ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==============================
# LOGIN ROUTE
# ==============================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data sent"
            }), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Missing email or password"
            }), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        if user.password == password:
            return jsonify({
                "success": True,
                "message": "Login successful",
                "is_admin": user.is_admin,
                "username": user.username,
                "email": user.email
            }), 200

        return jsonify({
            "success": False,
            "message": "Invalid password"
        }), 401

    except Exception as e:
        print("LOGIN ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
# ==============================
# ADMIN - GET ALL NOTES
# ==============================
@app.route("/admin/notes", methods=["GET"])
def admin_get_notes():
    notes = Notes.query.order_by(Notes.created_at.desc()).all()

    return jsonify([
        {
            "id": n.id,
            "subject": n.subject,
            "topic": n.topic,
            "content": n.content,
            "created_by": n.created_by or "Unknown",
            "created_at": n.created_at.isoformat() if n.created_at else None
        }
        for n in notes
    ]), 200


# ==============================
# ADMIN - GET ALL QUIZZES
# ==============================
@app.route("/admin/quizzes", methods=["GET"])
def admin_get_quizzes():
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()

    return jsonify([
        {
            "id": q.id,
            "title": q.title,
            "content": q.content,
            "created_by": q.created_by or "Unknown",
            "marks": q.marks,
            "attempted": q.attempted,
            "created_at": q.created_at.isoformat() if q.created_at else None,
            "submitted_at": q.submitted_at.isoformat() if q.submitted_at else None
        }
        for q in quizzes
    ]), 200

# ==============================
# ADD ADMIN
# ==============================
@app.route("/admin/promote_user/<int:user_id>", methods=["POST"])
def promote_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    user.is_admin = 1
    db.session.commit()
    return jsonify({"success": True, "message": f"{user.email} is now an admin"})

# ==============================
# DEMOTE ADMIN
# ==============================
@app.route("/admin/demote_user/<int:user_id>", methods=["POST"])
def demote_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    user.is_admin = 0
    db.session.commit()
    return jsonify({"success": True, "message": f"{user.email} is no longer an admin"})

# ==============================
# UPDATE PROFILE
# ==============================
@app.route("/update_profile", methods=["POST"])
def update_profile():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data sent"
            }), 400

        email = data.get("email")
        username = data.get("username")

        if not email or not username:
            return jsonify({
                "success": False,
                "message": "Missing email or username"
            }), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        user.username = username
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Profile updated successfully"
        }), 200

    except Exception as e:
        print("UPDATE PROFILE ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==============================
# CHANGE PASSWORD
# ==============================
@app.route("/change_password", methods=["POST"])
def change_password():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data sent"
            }), 400

        email = data.get("email")
        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if not email or not current_password or not new_password:
            return jsonify({
                "success": False,
                "message": "Missing fields"
            }), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        if user.password != current_password:
            return jsonify({
                "success": False,
                "message": "Current password incorrect"
            }), 400

        user.password = new_password
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Password updated successfully"
        }), 200

    except Exception as e:
        print("CHANGE PASSWORD ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==============================
# FORGOT PASSWORD
# ==============================
@app.route("/forgot_password", methods=["POST"])
def forgot_password():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data sent"
            }), 400

        email = data.get("email")

        if not email:
            return jsonify({
                "success": False,
                "message": "Invalid email"
            }), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "Email not found"
            }), 404

        subject = "Flowly Password Reset"

        body = f"""
Hello,

We received a request to reset your password.

Click the link below to reset it:

http://127.0.0.1:5500/test/resetpassword.html?email={email}

If you did not request this,
please ignore this email.

- Flowly Team
"""

        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()

        return jsonify({
            "success": True,
            "message": "Reset email sent successfully"
        }), 200

    except Exception as e:
        print("EMAIL ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Failed to send email"
        }), 500


# ==============================
# RESET PASSWORD
# ==============================
@app.route("/reset_password", methods=["POST"])
def reset_password():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data sent"
            }), 400

        email = data.get("email")
        new_password = data.get("new_password")

        if not email or not new_password:
            return jsonify({
                "success": False,
                "message": "Missing email or new password"
            }), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        user.password = new_password
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Password reset successful"
        }), 200

    except Exception as e:
        print("RESET PASSWORD ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==============================
# ADD COURSEWORK
# ==============================
@app.route("/add_coursework", methods=["POST"])
def add_coursework():
    try:
        data = request.get_json(force=True)

        if not data or "title" not in data or "due_date" not in data:
            return jsonify({
                "success": False,
                "message": "Invalid input"
            }), 400

        due_date_obj = datetime.strptime(data["due_date"], "%Y-%m-%d").date()

        email = data.get("email")

        task = Coursework(
            title=data["title"],
            description=data.get("description", ""),
            due_date=due_date_obj,
            status=data.get("status", "In Progress"),
            created_by=email
        )

        db.session.add(task)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Coursework added successfully"
        }), 200

    except Exception as e:
        print("ADD COURSEWORK ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==============================
# LOAD COURSEWORK
# ==============================
@app.route("/coursework", methods=["GET"])
def get_coursework():

    email = request.args.get("email")

    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400

    tasks = Coursework.query.filter_by(
        created_by=email
    ).order_by(
        Coursework.due_date.asc()
    ).all()

    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "due_date": t.due_date.strftime("%Y-%m-%d"),
            "status": t.status
        }
        for t in tasks
    ]), 200


# ==============================
# DELETE COURSEWORK
# ==============================
@app.route("/delete_coursework/<int:id>", methods=["DELETE"])
def delete_coursework(id):

    email = request.args.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400

    task = Coursework.query.filter_by(
        id=id,
        created_by=email
    ).first()

    if not task:
        return jsonify({
            "success": False,
            "message": "Coursework not found or you don't have permission to delete it."
        }), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Deleted successfully"
    }), 200

# ==============================
# GET UPCOMING COURSEWORK
# ==============================
@app.route("/upcoming", methods=["GET"])
def upcoming():

    email = request.args.get("email")

    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400

    today = datetime.now().date()

    tasks = Coursework.query.filter_by(
        created_by=email
    ).all()

    result = []

    for t in tasks:

        days_left = (t.due_date - today).days

        if days_left >= 0:
            result.append({
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "due_date": t.due_date.strftime("%Y-%m-%d"),
                "days_left": days_left,
                "status": t.status
            })

    result.sort(key=lambda x: x["days_left"])

    return jsonify(result), 200

# ==============================
# URGENT ALERTS
# ==============================
@app.route("/alerts", methods=["GET"])
def alerts():
    tasks = Coursework.query.all()
    today = datetime.now().date()

    result = []

    for t in tasks:
        days_left = (t.due_date - today).days

        if 0 <= days_left <= 3:
            result.append({
                "id": t.id,
                "title": t.title,
                "days_left": days_left,
                "status": "URGENT ⚠️"
            })

    return jsonify(result), 200


# ==============================
# OVERDUE TASKS
# ==============================
@app.route("/overdue", methods=["GET"])
def overdue():
    tasks = Coursework.query.all()
    today = datetime.now().date()

    result = []

    for t in tasks:
        days_left = (t.due_date - today).days

        if days_left < 0:
            result.append({
                "id": t.id,
                "title": t.title,
                "due_date": t.due_date.strftime("%Y-%m-%d"),
                "status": "OVERDUE ❌"
            })

    return jsonify(result), 200


# ==============================
# ADD MEMBER
# ==============================
@app.route("/add_member", methods=["POST"])
def add_member():
    try:
        data = request.get_json()

        if not data or "name" not in data:
            return jsonify({
                "success": False,
                "message": "Invalid input"
            }), 400

        member = Member(
            name=data["name"],
            email=data.get("email", ""),
            role=data.get("role", ""),
            coursework_id=data.get("coursework_id")
        )

        db.session.add(member)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Member added successfully"
        }), 200

    except Exception as e:
        print("ADD MEMBER ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==============================
# GET ALL MEMBERS
# ==============================
@app.route("/all_members", methods=["GET"])
def all_members():
    members = Member.query.all()

    return jsonify([
        {
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "role": m.role,
            "coursework_id": m.coursework_id
        }
        for m in members
    ]), 200


# ==============================
# AI NOTE SUMMARIZER
# ==============================
@app.route("/summarize_notes", methods=["POST"])
def summarize_notes():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data sent"
            }), 400

        notes = data.get("notes")

        if not notes:
            return jsonify({
                "success": False,
                "message": "No notes provided"
            }), 400

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a study assistant that summarizes notes clearly for students."
                },
                {
                    "role": "user",
                    "content": f"Summarize these notes:\n\n{notes}"
                }
            ]
        )

        summary = response.choices[0].message.content

        return jsonify({
            "success": True,
            "summary": summary
        }), 200

    except Exception as e:
        print("SUMMARIZE NOTES ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==============================
# GENERATE NOTES FROM PDF
# ==============================
@app.route("/generate_notes_from_file", methods=["POST"])
def generate_notes_from_file():

    print("FILES:", request.files)
    print("FORM:", request.form)
    
    try:
        if "pdf" not in request.files:
            return jsonify({
                "success": False,
                "message": "No PDF uploaded"
            }), 400

        pdf = request.files["pdf"]
        subject = request.form.get("subject", "")
        topic = request.form.get("topic", "")
        email = request.form.get("email", "")  # who is generating this note

        text = ""

        pdf_document = fitz.open(
            stream=pdf.read(),
            filetype="pdf"
        )

        for page in pdf_document:
            text += page.get_text()

        if not text.strip():
            return jsonify({
                "success": False,
                "message": "No text found in PDF"
            }), 400

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": """
You are an expert study assistant.

Create organized study notes with:
- Headings
- Bullet points
- Key concepts
- Important definitions
- Simple explanations

Make the notes easy for students to revise.
"""
                },
                {
                    "role": "user",
                    "content": f"""
Generate study notes from this material.

Subject: {subject}
Topic: {topic}

Material:
{text[:12000]}
"""
                }
            ]
        )

        notes = response.choices[0].message.content

        new_note = Notes(
            subject=subject,
            topic=topic,
            content=notes,
            created_by=email
        )

        db.session.add(new_note)
        db.session.commit()

        return jsonify({
            "success": True,
            "notes": notes
        }), 200

    except Exception as e:
        print("GENERATE NOTES ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==============================
# LOAD SAVED NOTES
# ==============================
@app.route("/notes", methods=["GET"])
def get_notes():

    email = request.args.get("email")

    notes = Notes.query.filter_by(
        created_by=email
    ).order_by(
        Notes.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": n.id,
            "subject": n.subject,
            "topic": n.topic,
            "content": n.content,
            "created_by": n.created_by or "Unknown"
        }
        for n in notes
    ]), 200
# ==============================
# SAVE MANUAL EDITS INTO SQLITE
# ==============================

@app.route("/save_note", methods=["POST"])
def save_note():
    try:
        data = request.get_json()

        subject = data.get("subject", "").strip()
        topic = data.get("topic", "").strip()
        content = data.get("content", "").strip()
        email = data.get("email", "").strip()

        if not subject or not topic or not content:
            return jsonify({
                "success": False,
                "message": "Missing subject, topic, or content"
            }), 400

        new_note = Notes(
            subject=subject,
            topic=topic,
            content=content,
            created_by=email
        )

        db.session.add(new_note)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Note saved successfully"
        }), 200

    except Exception as e:
        print("SAVE NOTE ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ==============================
# QUIZ TEXT PARSER
# ==============================
def parse_quiz_text(raw_text):
    """
    Parses the AI's raw quiz text (format below) into a list of
    {question, options, answer} dicts for the frontend.

    Q1. Question text?
    A. option 1
    B. option 2
    C. option 3
    D. option 4
    Answer: B
    """
    questions = []

    # Split into chunks starting at each "Q<number>."
    blocks = re.split(r"(?=Q\d+\.)", raw_text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Question text: everything after "Q1." up to the first option line
        q_match = re.search(r"Q\d+\.\s*(.+?)\s*(?=\n[A-D]\.)", block, re.DOTALL)
        if not q_match:
            continue
        question_text = q_match.group(1).strip().replace("\n", " ")

        # Options A-D
        option_matches = re.findall(r"^[A-D]\.\s*(.+)$", block, re.MULTILINE)
        if len(option_matches) < 4:
            continue
        options = [opt.strip() for opt in option_matches[:4]]

        # Answer letter -> map to actual option text
        answer_match = re.search(r"Answer:\s*([A-D])", block)
        if not answer_match:
            continue
        answer_letter = answer_match.group(1).strip().upper()
        letter_index = {"A": 0, "B": 1, "C": 2, "D": 3}[answer_letter]
        answer_text = options[letter_index]

        questions.append({
            "question": question_text,
            "options": options,
            "answer": answer_text
        })

    return questions


# ==============================
# GENERATE QUIZ FROM PDF
# ==============================
@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():
    try:
        if "pdf" not in request.files:
            return jsonify({
                "success": False,
                "message": "No PDF uploaded"
            }), 400

        pdf = request.files["pdf"]

        difficulty = request.form.get("difficulty", "Medium")
        question_count = request.form.get("questionCount", "10")
        email = request.form.get("email", "")  # who is generating this quiz

        text = ""

        pdf_document = fitz.open(
            stream=pdf.read(),
            filetype="pdf"
        )

        for page in pdf_document:
            text += page.get_text()

        if not text.strip():
            return jsonify({
                "success": False,
                "message": "No text found in PDF"
            }), 400

        prompt = f"""
Generate {question_count} multiple-choice questions.

STRICT FORMAT:

Q1. Question text?
A. option 1
B. option 2
C. option 3
D. option 4
Answer: B

Q2. Question text?
A. option 1
B. option 2
C. option 3
D. option 4
Answer: C

Rules:
- Difficulty: {difficulty}
- No explanations
- No markdown
- No headings
- Only questions in this format
- Always include Answer line

Notes:
{text[:12000]}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        raw_quiz_text = response.choices[0].message.content
        structured_quiz = parse_quiz_text(raw_quiz_text)
        total_questions = len(structured_quiz)

        # Save the raw text for the admin panel / records
        new_quiz = Quiz(
        title=f"{difficulty} Quiz",
        content=raw_quiz_text,
        created_by=email,
        marks=f"0/{total_questions}"
        )

        db.session.add(new_quiz)
        db.session.commit()

        # Parse into structured JSON for the frontend's interactive quiz UI
        structured_quiz = parse_quiz_text(raw_quiz_text)

        if not structured_quiz:
            return jsonify({
                "success": False,
                "message": "Quiz generated but could not be parsed. Try again."
            }), 500

        return jsonify({
        "success": True,
        "quiz": structured_quiz,
        "quiz_id": new_quiz.id   # ADD THIS
        }), 200

    except Exception as e:
        print("QUIZ ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==============================
# LOAD SAVED QUIZZES
# ==============================
@app.route("/quizzes", methods=["GET"])
def get_quizzes():
    email = request.args.get("email")

    if not email:
      return jsonify([]), 200

    quizzes = Quiz.query.filter_by(
        created_by=email
    ).order_by(
        Quiz.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": q.id,
            "title": q.title,
            "content": q.content,
            "created_by": q.created_by or "Unknown",
            "marks": q.marks,
            "attempted": q.attempted,
            "created_at": q.created_at.isoformat() if q.created_at else None,
            "submitted_at": q.submitted_at.isoformat() if q.submitted_at else None
        }
        for q in quizzes
    ]), 200

# ==============================
# SUBMIT QUIZZES
# ==============================
@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    try:
        data = request.get_json(force=True, silent=True)

        if not data:
            return jsonify({"success": False, "message": "No data received"}), 400

        quiz_id = data.get("quiz_id")
        score = data.get("score")
        total = data.get("total")

        quiz = Quiz.query.get(quiz_id)

        if not quiz:
            return jsonify({"success": False, "message": "Quiz not found"}), 404

        quiz.marks = f"{score}/{total}"
        quiz.attempted = True
        quiz.submitted_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Score saved"
        }), 200

    except Exception as e:
        print("SUBMIT QUIZ ERROR:", e)
        return jsonify({"success": False, "message": str(e)}), 500
    
# ==============================
# DELETE NOTE
# ==============================
@app.route("/delete_note", methods=["DELETE"])
def delete_note():
    note_id = request.args.get("id")
    email = request.args.get("email")

    if not note_id or not email:
        return jsonify({"success": False, "message": "Missing id or email"}), 400

    note = Notes.query.filter_by(id=note_id, created_by=email).first()

    if not note:
        return jsonify({"success": False, "message": "Note not found or you don't have permission"}), 404

    db.session.delete(note)
    db.session.commit()

    return jsonify({"success": True, "message": "Note deleted"}), 200

# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)