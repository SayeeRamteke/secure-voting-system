from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from blake3 import blake3
from datetime import datetime
import db, detection
from crypto.crypto_core import (
    verify_signature, compute_nullifier, hash_leaf, seal_vote
)
from crypto.merkle import MerkleTree

router = APIRouter()
merkle_tree = MerkleTree()   # in-memory; rebuilt from DB on startup (see main.py)

class VoteCompleteReq(BaseModel):
    credential_id: str
    voter_secret: str
    encrypted_vote: bytes   # AES-256-GCM sealed, from client
    aes_key: bytes          # wrapped with election pubkey (simplified: pass raw for demo)
    aes_nonce: bytes
    signature: bytes        # Ed25519 over encrypted_vote
    webauthn_assertion: dict

@router.post("/vote/begin")
async def vote_begin(request: Request):
    from webauthn import generate_authentication_options
    import base64
    opts = generate_authentication_options(rp_id="localhost")
    request.session["vote_challenge"] = base64.b64encode(opts.challenge).decode()
    return {
        "challenge": base64.b64encode(opts.challenge).decode(),
        "rpId": "localhost",
        "timeout": 60000,
        "userVerification": "required"
    }

@router.post("/vote/complete")
async def vote_complete(req: VoteCompleteReq, request: Request):
    # 1. look up voter by credential_id first
    voter = db.get_voter_by_credential(req.credential_id)
    if not voter:
        raise HTTPException(404, "Voter not found")

    # 2. verify WebAuthn assertion
    from webauthn import verify_authentication_response
    import base64
    try:
        verify_authentication_response(
            credential=req.webauthn_assertion,
            expected_challenge=base64.b64decode(request.session.get("vote_challenge", "")),
            expected_rp_id="localhost",
            expected_origin="http://localhost:5173",
            credential_public_key=bytes(voter["public_key"]),
            credential_current_sign_count=0,
        )
    except Exception as e:
        print(f"WebAuthn error: {e}")
        raise HTTPException(401, f"WebAuthn failed: {e}")

    # 3. verify BLAKE3(voter_secret) == stored hash
    if blake3(req.voter_secret.encode()).hexdigest() != voter["voter_secret_hash"]:
        raise HTTPException(403, "voter_secret mismatch")

    # 4. compute nullifier
    nullifier = compute_nullifier(req.voter_secret, "election_2024")

    # 5. atomic insert — UNIQUE(nullifier) rejects double vote
    try:
        db.insert_vote(
            nullifier=nullifier,
            encrypted_vote=req.encrypted_vote,
            aes_key=req.aes_key,
            aes_nonce=req.aes_nonce,
            signature=req.signature,
            leaf=""
        )
    except Exception:
        raise HTTPException(409, "Already voted")

    # 6. compute and store merkle leaf
    ts = datetime.utcnow().isoformat()
    leaf = hash_leaf(nullifier, req.encrypted_vote, ts)
    merkle_tree.insert(leaf)

    import sqlite3
    conn = sqlite3.connect("voting.db")
    conn.execute("UPDATE votes SET merkle_leaf=?, timestamp=? WHERE nullifier=?",
                 (leaf, ts, nullifier))
    conn.commit()

    # 7. run detection + store new root
    detection.verify_chain()
    new_root = merkle_tree.get_root()
    db.insert_root(new_root, db.vote_count())

    return {"leaf_index": len(merkle_tree.leaves) - 1}