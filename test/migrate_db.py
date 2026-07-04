import sqlite3
import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "database.db")

if not os.path.exists(db_path):
    print(f"No database.db found at {db_path} — nothing to migrate.")
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
    print(f"Added '{column}' to '{table}'.")


# ==========================
# Existing migrations
# ==========================
add_column_if_missing("notes", "created_by")
add_column_if_missing("quiz", "created_by")
add_column_if_missing("quiz", "marks", "INTEGER")
add_column_if_missing("quiz", "attempted", "BOOLEAN DEFAULT 0")
add_column_if_missing("quiz", "submitted_at", "DATETIME")

# ==========================
# New migration
# ==========================
add_column_if_missing("coursework", "created_by")

# ==========================
# Remove Member table
# ==========================
cursor.execute("DROP TABLE IF EXISTS member")
print("Removed 'member' table (if it existed).")

conn.commit()
conn.close()

print("Migration complete!")