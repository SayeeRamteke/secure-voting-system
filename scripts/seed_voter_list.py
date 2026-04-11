import sqlite3
from datetime import datetime

DB_PATH = "../backend/voting.db"


def seed_voters():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Replace with your actual roll numbers
    voters = [
        ("101",),
        ("102",),
        ("103",),
        ("104",),
        ("105",)
    ]

    for voter in voters:
        try:
            cursor.execute(
                "INSERT INTO voter_list (roll_no, is_enrolled) VALUES (?, 0)",
                voter
            )
        except sqlite3.IntegrityError:
            # already exists
            pass

    conn.commit()
    conn.close()

    print("✅ Voter list seeded successfully")


if __name__ == "__main__":
    seed_voters()