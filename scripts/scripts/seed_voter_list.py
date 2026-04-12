import sqlite3
import os

DB_PATH = "../backend/votes.db"

# List of fake voters to seed
VOTERS = [
    {"roll_no": "CS2021001", "name": "Priya Sharma"},
    {"roll_no": "CS2021002", "name": "Rahul Verma"},
    {"roll_no": "CS2021003", "name": "Anita Desai"},
    {"roll_no": "CS2021004", "name": "Arjun Mehta"},
    {"roll_no": "CS2021005", "name": "Sneha Patil"},
]

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

# Create voter list table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS voter_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        is_registered INTEGER DEFAULT 0,
        has_voted INTEGER DEFAULT 0
    )
""")

# Insert voters
for voter in VOTERS:
    try:
        cursor.execute(
            "INSERT INTO voter_list (roll_no, name) VALUES (?, ?)",
            (voter["roll_no"], voter["name"])
        )
        print(f"Added voter: {voter['roll_no']} — {voter['name']}")
    except sqlite3.IntegrityError:
        print(f"Already exists: {voter['roll_no']} — skipping")

db.commit()
db.close()
print(f"\nDone! {len(VOTERS)} voters seeded into database.")