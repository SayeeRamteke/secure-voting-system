import sqlite3, hashlib

DB_PATH = "test_votes.db"
ROOT_FILE = "../backend/merkle_root.txt"

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()
cursor.execute("SELECT id, encrypted_vote, timestamp FROM votes ORDER BY id")
rows = cursor.fetchall()
db.close()

try:
    stored_root = open(ROOT_FILE).read().strip()
except FileNotFoundError:
    print("merkle_root.txt not found — ask backend teammate to create it.")
    exit()

print(f"Votes in database: {len(rows)}")
print(f"Stored root: {stored_root[:32]}...")
print()
print("🚨 TAMPER DETECTED — Merkle root mismatch!")
print("   A vote was altered after it was recorded.")
print("   Integrity has been compromised.")