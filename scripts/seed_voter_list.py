import sqlite3, sys
DB_PATH = "../backend/votes.db"
ROLL_NOS = sys.argv[1:]  # pass as: python seed_voter_list.py 101 102 103

conn = sqlite3.connect("voting.db")
conn.execute("""
CREATE TABLE IF NOT EXISTS voter_list (
    roll_no TEXT PRIMARY KEY
)
""")
for r in ROLL_NOS:
    conn.execute("INSERT OR IGNORE INTO voter_list VALUES (?)", (r,))
conn.commit()
print(f"Seeded {len(ROLL_NOS)} voters: {ROLL_NOS}")