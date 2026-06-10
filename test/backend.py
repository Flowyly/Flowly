# ==============================
# IMPORT LIBRARIES
# ==============================
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import fitz
import traceback
import os  # FIX: added for absolute database path

# ==============================
# CREATE FLASK APP
# ==============================
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ==============================
# SQLITE CONFIGURATION
# ==============================

# FIX: get absolute path of current folder (Harith folder)
basedir = os.path.abspath(os.path.dirname(__file__))

print("DATABASE PATH:", os.path.join(basedir, "database.db"))

# FIX: ensures database.db is always correctly linked
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==============================
# GROQ CONFIG
# ==============================
load_dotenv(dotenv_path=os.path.join(basedir, ".env"))

api_key = os.getenv("GROQ_API_KEY", "").strip()

if not api_key:
    print("WARNING: GROQ_API_KEY not found in .env")

client = Groq(api_key=api_key)

# ------------------------------
# USER TABLE
# ------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    
# ------------------------------
# NOTE TABLE
# ------------------------------
class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    subject = db.Column(db.String(100))
    topic = db.Column(db.String(200))

    content = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

# ------------------------------
# QUIZ TABLE
# ------------------------------
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))

    content = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    ) 

# ------------------------------
# COURSEWORK TABLE (PARENT)
# ------------------------------
class Coursework(db.Model):
    __tablename__ = "coursework"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(300))
    
    # FIX: use proper DATE type instead of string
    due_date = db.Column(db.Date, nullable=False)

    status = db.Column(db.String(20), default="In Progress")

    # RELATIONSHIP: one coursework has many members
    members = db.relationship('Member', backref='coursework', lazy=True)


# ------------------------------
# MEMBER TABLE (CHILD)
# ------------------------------
class Member(db.Model):
    __tablename__ = "member"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    role = db.Column(db.String(50))

    # FIX: proper foreign key relationship
    coursework_id = db.Column(db.Integer, db.ForeignKey('coursework.id'))

# ==============================
# CREATE DATABASE (RUN ONCE ONLY)
# ==============================
# IMPORTANT:
# Run this ONCE manually or via separate init script, then comment it back.

#with app.app_context():
#    db.create_all()
# ==============================
# AI NOTE SUMMARIZER
# ==============================
@app.route("/generate_notes_from_file", methods=["POST"])
def generate_notes_from_file():

    if "file" not in request.files:
        return jsonify({
            "success": False,
            "message": "No PDF uploaded"
        }), 400

    pdf = request.files["file"]

    text = ""

    try:

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
Generate study notes from this material:

{text[:12000]}
"""
                }
            ]
        )

        summary = response.choices[0].message.content
        subject = request.form.get("subject", "")
        topic = request.form.get("topic", "")

        new_note = Notes(
        subject=subject,
        topic=topic,
        content=summary
)
        db.session.add(new_note)
        db.session.commit()

        return jsonify({
            "success": True,
            "notes": summary
        }), 200

    except Exception as e:

        print("NOTES ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
# ==============================
# API to load notes
# ==============================
@app.route("/notes", methods=["GET"])
def get_notes():

    notes = Notes.query.order_by(
        Notes.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": n.id,
            "subject": n.subject,
            "topic": n.topic,
            "content": n.content
        }
        for n in notes
    ])

# ==============================
# AI QUIZ GENERATOR
# ==============================
@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():

    if "pdf" not in request.files:
        return jsonify({
            "success": False,
            "message": "No PDF uploaded"
        }), 400

    pdf = request.files["pdf"]

    difficulty = request.form.get("difficulty", "Medium")
    question_count = request.form.get("questionCount", "10")

    text = ""

    pdf_document = fitz.open(
        stream=pdf.read(),
        filetype="pdf"
    )

    for page in pdf_document:
        text += page.get_text()

    prompt = f"""
Generate {question_count} multiple-choice questions.

STRICT FORMAT (VERY IMPORTANT):

Q1. Question text?
A. option 1
B. option 2
C. option 3
D. option 4
Answer: B

Q2. Question text?
A. ...
B. ...
C. ...
D. ...
Answer: C

Rules:
- No explanations
- No markdown
- No headings
- Only questions in this format
- Always include Answer line

Notes:
{text[:12000]}
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        quiz = response.choices[0].message.content
        new_quiz = Quiz(
        title=f"{difficulty} Quiz",
        content=quiz
)

        db.session.add(new_quiz)
        db.session.commit()

        return jsonify({
            "success": True,
            "quiz": quiz
        })

    except Exception as e:

        print("QUIZ ERROR:", e)
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
# ==============================
# API to load quizzes
# ==============================
@app.route("/quizzes", methods=["GET"])
def get_quizzes():

    quizzes = Quiz.query.order_by(
        Quiz.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": q.id,
            "title": q.title,
            "content": q.content
        }
        for q in quizzes
    ])

# ==============================
# HOME ROUTE
# ==============================
@app.route("/")
def home():
    return "Flowly Backend with Proper SQLite Running 🚀"


# ==============================
# ADD MEMBER
# ==============================
@app.route("/add_member", methods=["POST"])
def add_member():
    data = request.get_json()  # FIX: safer than request.json

    if not data or "name" not in data:
        return jsonify({"error": "Invalid input"}), 400

    member = Member(
        name=data["name"],
        email=data.get("email", ""),
        role=data.get("role", ""),
        coursework_id=data.get("coursework_id")
    )

    db.session.add(member)
    db.session.commit()

    return jsonify({"message": "Member added successfully"}), 200


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
# REGISTER ROUTE
# ==============================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No data sent"}), 400

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
        return jsonify({"success": False, "message": "Email already exists"}), 400

    new_user = User(
        username=username,
        email=email,
        password=generate_password_hash(password)
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"success": True, "message": "Registration successful"}), 200
# ==============================
# ADD COURSEWORK
# ==============================
@app.route("/add_coursework", methods=["POST"])
def add_coursework():

    # DEBUG: raw incoming request
    print("RAW DATA:", request.data)

    # FIX: force JSON parsing (important for your issue)
    data = request.get_json(force=True)

    print("DATA RECEIVED:", data)  # ✅ DEBUG CHECKPOINT

    if not data or "title" not in data or "due_date" not in data:
        return jsonify({"error": "Invalid input"}), 400

    # Convert string → date object
    due_date_obj = datetime.strptime(data["due_date"], "%Y-%m-%d").date()

    task = Coursework(
        title=data["title"],
        description=data.get("description", ""),
        due_date=due_date_obj,
        status=data.get("status", "In Progress")
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Coursework added successfully"}), 200

# ==============================
# LOAD COURSEWORK
# ==============================
@app.route("/coursework", methods=["GET"])
def get_coursework():

    tasks = Coursework.query.all()

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
    task = Coursework.query.get(id)

    if not task:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Deleted successfully"}), 200

# ==============================
# GET ALL COURSEWORK (WITH DAYS LEFT)
# ==============================
@app.route("/upcoming", methods=["GET"])
def upcoming():
    tasks = Coursework.query.all()
    today = datetime.now().date()

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
# URGENT ALERTS (0–3 DAYS)
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
# LOGIN
# ==============================
@app.route("/login", methods=["POST"])
def login():
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

    if check_password_hash(user.password, password):
        return jsonify({
            "success": True,
            "message": "Login successful"
        }), 200

    return jsonify({
        "success": False,
        "message": "Invalid password"
    }), 401
# ==============================
# EMAIL CONFIGURATION
# ==============================

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    print("WARNING: Email credentials missing")

# ==============================
# UPDATE PROFILE
# ==============================
@app.route("/update_profile", methods=["POST"])
def update_profile():
    data = request.get_json()

    # ✅ ADD HERE
    if not data:
        return jsonify({
            "success": False,
            "message": "No data sent"
        }), 400

    email = data.get("email")
    username = data.get("username")

    user = User.query.filter_by(email=email).first()

    if not user:

        return jsonify({
            "success": False,
            "message": "User not found"
        }), 400

    user.username = username

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Profile updated successfully"
    }), 200


# ==============================
# CHANGE PASSWORD
# ==============================
@app.route("/change_password", methods=["POST"])
def change_password():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data sent"
        }), 400

    email = data.get("email")
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    if not check_password_hash(user.password, current_password):
        return jsonify({
            "success": False,
            "message": "Current password incorrect"
        }), 400

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Password updated successfully"
    }), 200
# ==============================
# FORGOT PASSWORD
# ==============================
@app.route("/forgot_password", methods=["POST"])
def forgot_password():

    data = request.get_json()

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

    try:

        # ==============================
        # EMAIL CONTENT
        # ==============================

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

        # ==============================
        # CREATE EMAIL
        # ==============================

        msg = MIMEMultipart()

        msg["From"] = EMAIL_ADDRESS
        msg["To"] = email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # ==============================
        # CONNECT TO GMAIL SMTP
        # ==============================

        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        # ==============================
        # SEND EMAIL
        # ==============================

        server.sendmail(
            EMAIL_ADDRESS,
            email,
            msg.as_string()
        )

        server.quit()

        return jsonify({
            "success": True,
            "message": "Reset email sent successfully"
        }), 200

    except Exception as e:

        print("EMAIL ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to send email"
        }), 500

# ==============================
# FORGOT PASSWORD - RESET
# ==============================
@app.route("/reset_password", methods=["POST"])
def reset_password():

    data = request.get_json()

    email = data.get("email")
    new_password = data.get("new_password")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    user.password = generate_password_hash(new_password)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Password reset successful"
    }), 200
# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)