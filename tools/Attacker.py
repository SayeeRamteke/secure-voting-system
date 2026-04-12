import sqlite3

# Update this path once your backend teammate shares their folder location
DB_PATH = "test_votes.db"

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

cursor.execute("SELECT id, encrypted_vote FROM votes LIMIT 1")
row = cursor.fetchone()

if not row:
    print("No votes found. Make sure backend is running and someone has voted.")
    exit()

vote_id, blob = row
print(f"Found vote ID: {vote_id}")
print(f"Original bytes: {blob[:10].hex()}")

tampered = bytearray(blob)
tampered[10] ^= 0xFF
cursor.execute("UPDATE votes SET encrypted_vote = ? WHERE id = ?", (bytes(tampered), vote_id))
db.commit()
db.close()
print(f"Vote {vote_id} tampered! Run Defender.py to detect it.")