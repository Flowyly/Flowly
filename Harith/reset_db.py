from backend import db, app

with app.app_context():
    db.drop_all()   # deletes old tables
    db.create_all() # creates fresh correct tables

print("Database reset complete 🚀")