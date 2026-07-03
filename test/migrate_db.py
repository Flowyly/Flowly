# ==============================
# ONE-TIME MIGRATION SCRIPT
# Adds the missing columns to the existing
# notes and quiz tables, WITHOUT deleting your existing data.
#
# Run this once: python migrate_db.py
# Then start your backend normally: python backend.py
# ==============================
import sqlite3
import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "database.db")

if not os.path.exists(db_path):
    print(f"No database.db found at {db_path} — nothing to migrate.")
    print("Just run backend.py normally; it will create a fresh database.")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()


def add_column_if_missing(table, column, col_type="VARCHAR(100)"):
    cursor.execute(f"PRAGMA table_info({table})")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if column in existing_columns:
        print(f"'{column}' already exists on '{table}' — skipping.")
        return

    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    print(f"Added '{column}' column to '{table}'.")


add_column_if_missing("notes", "created_by")
add_column_if_missing("quiz", "created_by")
add_column_if_missing("quiz", "marks", "INTEGER")

# ---- New columns for dashboard's "today's quiz results" feature ----
add_column_if_missing("quiz", "attempted", "BOOLEAN DEFAULT 0")
add_column_if_missing("quiz", "submitted_at", "DATETIME")

conn.commit()
conn.close()

print("Migration complete. Your existing users/notes/quizzes are untouched.")
print("Old notes/quizzes will show 'Unknown' as the creator since they predate this change.")
print("Old quizzes will have attempted=0 and no submitted_at, so they won't appear on the dashboard until re-answered.")