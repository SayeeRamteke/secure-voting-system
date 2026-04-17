import sqlite3, os
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "votes.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def tx():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with tx() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS voter_list (
            roll_no TEXT PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS voters (
            roll_no           TEXT PRIMARY KEY,
            credential_id     TEXT UNIQUE NOT NULL,
            public_key        BLOB NOT NULL,
            voter_secret_hash TEXT NOT NULL,
            enrolled_at       TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS votes (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nullifier      TEXT UNIQUE NOT NULL,
            encrypted_vote BLOB NOT NULL,
            aes_key        BLOB NOT NULL,
            aes_nonce      BLOB NOT NULL,
            signature      BLOB NOT NULL,
            merkle_leaf    TEXT NOT NULL,
            timestamp      TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS merkle_roots (
            seq        INTEGER PRIMARY KEY AUTOINCREMENT,
            root_hash  TEXT NOT NULL,
            vote_count INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)

# ── helpers ─────────────────────────────────────────
def roll_exists(roll_no: str) -> bool:
    with get_conn() as c:
        return bool(c.execute(
            "SELECT 1 FROM voter_list WHERE roll_no=?", (roll_no,)).fetchone())

def get_voter_by_credential(credential_id: str):
    conn = get_conn()
    return conn.execute(
        "SELECT * FROM voters WHERE credential_id=?", (credential_id,)).fetchone()

def insert_vote(nullifier, encrypted_vote, aes_key, aes_nonce, signature, leaf):
    with tx() as conn:
        conn.execute(
            "INSERT INTO votes (nullifier,encrypted_vote,aes_key,aes_nonce,signature,merkle_leaf)"
            " VALUES (?,?,?,?,?,?)",
            (nullifier, encrypted_vote, aes_key, aes_nonce, signature, leaf))

def get_all_votes():
    conn = get_conn()
    return conn.execute("SELECT * FROM votes ORDER BY id").fetchall()

def get_latest_root() -> str | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT root_hash FROM merkle_roots ORDER BY seq DESC LIMIT 1").fetchone()
    return row["root_hash"] if row else None

def insert_root(root_hash: str, vote_count: int):
    with tx() as conn:
        conn.execute(
            "INSERT INTO merkle_roots (root_hash, vote_count) VALUES (?,?)",
            (root_hash, vote_count))

def vote_count() -> int:
    conn = get_conn()
    return conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]