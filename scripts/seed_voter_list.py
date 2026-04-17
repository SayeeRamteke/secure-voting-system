import sqlite3, sys, os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "backend", "votes.db")

ROLL_NOS = sys.argv[1:]

conn = sqlite3.connect(DB_PATH)

conn.execute("""
CREATE TABLE IF NOT EXISTS voter_list (
    roll_no TEXT PRIMARY KEY
)
""")

for r in ROLL_NOS:
    conn.execute("INSERT OR IGNORE INTO voter_list VALUES (?)", (r,))

conn.commit()
conn.close()