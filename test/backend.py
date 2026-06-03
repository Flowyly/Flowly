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
import os  # FIX: added for absolute database path

print("GROQ KEY:", os.getenv("T4J984v3W1jl5XLWSr8qWGdyb3FYWNV1kvRgd601dqDnicEJzVuS"))
# ==============================
# CREATE FLASK APP
# ==============================
app = Flask(__name__)
CORS(app)

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
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ==============================
# AI NOTE SUMMARIZER
# ==============================
@app.route("/summarize_notes", methods=["POST"])
def summarize_notes():

    data = request.get_json()

    notes = data.get("notes")

    if not notes:
        return jsonify({
            "success": False,
            "message": "No notes provided"
        })

    try:

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
        })

    except Exception as e:

        print(e)

        return jsonify({
            "success": False,
            "message": "AI summarization failed"
        })
    
# ==============================
# AI QUIZ GENERATOR
# ==============================
@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():

    data = request.get_json()

    notes = data.get("notes")

    if not notes:
        return jsonify({
            "success": False,
            "message": "No notes provided"
        })

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",

            messages=[
                {
                    "role": "system",
                    "content": "You are a quiz generator for students."
                },

                {
                    "role": "user",
                    "content": f"""
Generate 5 multiple choice questions (MCQ)
from these notes.

Format:

1. Question
A.
B.
C.
D.
Answer:

Notes:
{notes}
"""
                }
            ]
        )

        quiz = response.choices[0].message.content

        return jsonify({
            "success": True,
            "quiz": quiz
        })

    except Exception as e:

        print(e)

        return jsonify({
            "success": False,
            "message": "Quiz generation failed"
        })
    
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

    status = db.Column(db.String(20), default="Pending")

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

# ------------------------------
# USER TABLE
# ------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

# ==============================
# CREATE DATABASE (RUN ONCE ONLY)
# ==============================
# IMPORTANT:
# Run this ONCE manually or via separate init script, then comment it back.

with app.app_context():
    db.create_all()
    
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

    return jsonify({"message": "Member added successfully"})


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
    ])

# ==============================
# REGISTER ROUTE
# ==============================
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        print("REGISTER DATA:", data)

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return jsonify({
                "success": False,
                "message": "Missing fields"
            })

        # check if user exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return jsonify({
                "success": False,
                "message": "Email already exists"
            })

        # create user
        new_user = User(
    username=username,
    email=email,
    password=generate_password_hash(password)
)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Registration successful"
        })

    except Exception as e:
        print("REGISTER ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Server error"
        }), 500

    # ==============================
    # VALIDATION
    # ==============================

    if not username or not email or not password:

        return jsonify({
            "success": False,
            "message": "Missing fields"
        })

    # ==============================
    # CHECK IF EMAIL EXISTS
    # ==============================

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:

        return jsonify({
            "success": False,
            "message": "Email already registered"
        })

    # ==============================
    # CREATE NEW USER
    # ==============================

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
    })

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
        status="Pending"
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Coursework added successfully"})

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

    return jsonify({"message": "Deleted successfully"})

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
    return jsonify(result)


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

    return jsonify(result)


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

    return jsonify(result)

# ==============================
# LOGIN
# ==============================
@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user:

        return jsonify({
            "success": False,
            "message": "User not found"
        })

    # CHECK HASHED PASSWORD
    if check_password_hash(user.password, password):

        return jsonify({
            "success": True,
            "message": "Login successful"
        })

    return jsonify({
        "success": False,
        "message": "Invalid password"
    })
# ==============================
# EMAIL CONFIGURATION
# ==============================

EMAIL_ADDRESS = "muhdharris1207@gmail.com"
EMAIL_PASSWORD = "mufs wjxm tilh dgwv"

# ==============================
# UPDATE PROFILE
# ==============================
@app.route("/update_profile", methods=["POST"])
def update_profile():

    data = request.get_json()

    email = data.get("email")
    username = data.get("username")

    user = User.query.filter_by(email=email).first()

    if not user:

        return jsonify({
            "success": False,
            "message": "User not found"
        })

    user.username = username

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Profile updated successfully"
    })


# ==============================
# CHANGE PASSWORD
# ==============================
@app.route("/change_password", methods=["POST"])
def change_password():

    data = request.get_json()

    email = data.get("email")

    current_password = data.get("current_password")

    new_password = data.get("new_password")

    user = User.query.filter_by(email=email).first()

    if not user:

        return jsonify({
            "success": False,
            "message": "User not found"
        })

    if not check_password_hash(user.password, current_password):

        return jsonify({
            "success": False,
            "message": "Current password incorrect"
        })

    user.password = generate_password_hash(new_password)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Password updated successfully"
    })

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
        })

    try:

        # ==============================
        # EMAIL CONTENT
        # ==============================

        subject = "Flowly Password Reset"

        body = f"""
Hello,

We received a request to reset your password.

Click the link below to reset it:

http://127.0.0.1:5500/resetpassword.html

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
        })

    except Exception as e:

        print("EMAIL ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to send email"
        }) 
# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    app.run(debug=True)