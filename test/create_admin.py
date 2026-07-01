from backend import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Change these to your actual admin details
    admin_email = "admin@flowly.com"
    admin_username = "Admin"
    admin_password = "admin123"

    # Check if already exists
    existing = User.query.filter_by(email=admin_email).first()

    if existing:
        print("Admin already exists!")
    else:
        admin = User(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            is_admin=1  # 👈 This is what makes them admin
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created successfully! → {admin_email}")