import sqlite3

def get_db():
    conn = sqlite3.connect("voting.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Preloaded voter list (eligibility gate)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS voter_list (
        roll_no TEXT PRIMARY KEY,
        is_enrolled BOOLEAN DEFAULT 0,
        enrolled_at TIMESTAMP
    )
    """)

    # 2. Registered voters (after WebAuthn)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS voters (
        roll_no TEXT PRIMARY KEY,
        credential_id TEXT UNIQUE,
        public_key BLOB,
        voter_secret_hash TEXT,
        enrolled_at TIMESTAMP,
        FOREIGN KEY (roll_no) REFERENCES voter_list(roll_no)
    )
    """)

    # 3. Votes (ANONYMOUS — no roll_no, no credential_id)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nullifier TEXT UNIQUE,
        encrypted_vote BLOB,
        wrapped_aes_key BLOB,
        signature BLOB,
        merkle_leaf TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4. Merkle roots (append-only integrity log)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS merkle_roots (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        root_hash TEXT,
        vote_count INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()