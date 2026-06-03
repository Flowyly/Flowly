# PART 1 - IMPORTING TOOLS
from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, date

app = Flask(__name__)

# PART 2 - DATABASE FUNCTIONS
def init_db():  # initialise database
    conn = sqlite3.connect('database.db')  # connect to database
    cursor = conn.cursor()  # prepare tool to send SQL commands
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coursework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            due_date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# helper function to calculate days left
def calculate_days_left(due_date_str):
    due_date_obj = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    today = date.today()
    difference = (due_date_obj - today).days

    if difference > 0:
        return f"{difference} day(s) left"
    elif difference == 0:
        return "Due today"
    else:
        return f"Overdue by {abs(difference)} day(s)"


# PART 3 - DISPLAY SYSTEM
@app.route('/')
def home():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coursework ORDER BY due_date ASC")
    coursework_list = cursor.fetchall()
    conn.close()

    # create new list with extra days_left value
    coursework_with_days = []
    for item in coursework_list:
        days_left = calculate_days_left(item[3])
        coursework_with_days.append((item[0], item[1], item[2], item[3], days_left))

    return render_template('index.html', coursework_list=coursework_with_days)


# PART 4 - ADDING, DELETING AND EDITING COURSEWORK
@app.route('/add', methods=['POST'])
def add_coursework():
    title = request.form['title']
    description = request.form['description']
    due_date = request.form['due_date']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO coursework (title, description, due_date) VALUES (?, ?, ?)",
        (title, description, due_date)
    )
    conn.commit()
    conn.close()

    return redirect('/')


@app.route('/delete/<int:id>')
def delete_coursework(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM coursework WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect('/')


@app.route('/edit/<int:id>')
def edit_coursework(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coursework WHERE id = ?", (id,))
    coursework = cursor.fetchone()
    conn.close()

    return render_template('edit.html', coursework=coursework)


@app.route('/update/<int:id>', methods=['POST'])
def update_coursework(id):
    title = request.form['title']
    description = request.form['description']
    due_date = request.form['due_date']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE coursework
        SET title = ?, description = ?, due_date = ?
        WHERE id = ?
    """, (title, description, due_date, id))
    conn.commit()
    conn.close()

    return redirect('/')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)