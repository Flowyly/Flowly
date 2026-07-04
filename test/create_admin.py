from backend import app, db, User

with app.app_context():
    admin_email = "admin@flowly.com"
    admin_username = "Admin"
    admin_password = "admin123"

    existing = User.query.filter_by(email=admin_email).first()

    if existing:
        print("Admin already exists!")
    else:
        admin = User(
            username=admin_username,
            email=admin_email,
            password=admin_password,  # plaintext, matches login's comparison
            is_admin=1
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created successfully! → {admin_email}")