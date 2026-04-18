import base64
import sqlite3, os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "voting.db")
DB_PATH = os.path.abspath(DB_PATH)

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
        CREATE TABLE IF NOT EXISTS election_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            commitments TEXT NOT NULL
        );
        """)

# ── helpers ─────────────────────────────────────────
def roll_exists(roll_no: str) -> bool:
    with get_conn() as c:
        return bool(c.execute(
            "SELECT 1 FROM voter_list WHERE roll_no=?", (roll_no,)).fetchone())

def _decode_base64url(value: str) -> bytes | None:
    try:
        padded = value + "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(padded.encode())
    except Exception:
        return None

def get_voter_by_credential(credential_id: str | bytes):
    candidates = []
    if isinstance(credential_id, bytes):
        candidates.append(credential_id)
    else:
        candidates.append(credential_id)
        decoded = _decode_base64url(credential_id)
        if decoded:
            candidates.append(decoded)

    conn = get_conn()
    for candidate in candidates:
        row = conn.execute(
            "SELECT * FROM voters WHERE credential_id=?", (candidate,)).fetchone()
        if row:
            return row
    return None

def insert_vote(nullifier, encrypted_vote, aes_key, aes_nonce, signature, leaf):
    with tx() as conn:
        conn.execute(
            "INSERT INTO votes (nullifier,encrypted_vote,aes_key,aes_nonce,signature,merkle_leaf)"
            " VALUES (?,?,?,?,?,?)",
            (nullifier, encrypted_vote, aes_key, aes_nonce, signature, leaf))

def get_vote_by_nullifier(nullifier: str):
    conn = get_conn()
    return conn.execute(
        "SELECT * FROM votes WHERE nullifier=?", (nullifier,)).fetchone()

def get_vote_leaf_index(nullifier: str) -> int | None:
    conn = get_conn()
    rows = conn.execute("SELECT nullifier FROM votes ORDER BY id").fetchall()
    for index, row in enumerate(rows):
        if row["nullifier"] == nullifier:
            return index
    return None

def get_vote_by_leaf_index(leaf_index: int):
    conn = get_conn()
    return conn.execute(
        "SELECT * FROM votes ORDER BY id LIMIT 1 OFFSET ?", (leaf_index,)).fetchone()

def get_all_votes():
    conn = get_conn()
    return conn.execute("SELECT * FROM votes ORDER BY id").fetchall()

def get_latest_root() -> str | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT root_hash FROM merkle_roots ORDER BY seq DESC LIMIT 1").fetchone()
    return row["root_hash"] if row else None

def get_latest_root_record():
    conn = get_conn()
    return conn.execute(
        "SELECT root_hash, vote_count FROM merkle_roots ORDER BY seq DESC LIMIT 1"
    ).fetchone()

def insert_root(root_hash: str, vote_count: int):
    with tx() as conn:
        conn.execute(
            "INSERT INTO merkle_roots (root_hash, vote_count) VALUES (?,?)",
            (root_hash, vote_count))

def update_vote_leaf_timestamp(nullifier: str, leaf: str, timestamp: str):
    with tx() as conn:
        conn.execute(
            "UPDATE votes SET merkle_leaf=?, timestamp=? WHERE nullifier=?",
            (leaf, timestamp, nullifier))

def vote_count() -> int:
    conn = get_conn()
    return conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]

import json

def save_commitments(commitments_json: str):
    """Saves the Feldman VSS commitments. Called during startup."""
    with tx() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO election_config (id, commitments) VALUES (1, ?)",
            (commitments_json,)
        )

def get_election_commitments():
    """Retrieves commitments for shard verification in admin.py."""
    conn = get_conn()
    row = conn.execute("SELECT commitments FROM election_config WHERE id = 1").fetchone()
    if row:
        # We store it as a JSON string in the DB, so we decode it back to a list
        return json.loads(row["commitments"])
    return None