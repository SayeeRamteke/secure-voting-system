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
    opts = generate_authentication_options(rp_id="localhost")
    request.session["vote_challenge"] = opts.challenge
    return opts

@router.post("/vote/complete")
async def vote_complete(req: VoteCompleteReq, request: Request):
    # 1. verify WebAuthn assertion
    from webauthn import verify_authentication_response
    try:
        verify_authentication_response(
            credential=req.webauthn_assertion,
            expected_challenge=request.session.get("vote_challenge"),
            expected_rp_id="localhost",
            expected_origin="http://localhost:5173"
        )
    except Exception as e:
        raise HTTPException(401, f"WebAuthn failed: {e}")

    # 2. look up voter by credential_id
    voter = db.get_voter_by_credential(req.credential_id)
    if not voter:
        raise HTTPException(404, "Voter not found")

    # 3. verify BLAKE3(voter_secret) == stored hash
    if blake3(req.voter_secret.encode()).hexdigest() != voter["voter_secret_hash"]:
        raise HTTPException(403, "voter_secret mismatch")

    # 4. compute nullifier
    nullifier = compute_nullifier(req.voter_secret, "election_2024")

    # 5-8. atomic insert — UNIQUE(nullifier) rejects double vote
    try:
        db.insert_vote(
            nullifier       = nullifier,
            encrypted_vote  = req.encrypted_vote,
            aes_key         = req.aes_key,
            aes_nonce       = req.aes_nonce,
            signature       = req.signature,
            leaf            = ""   # placeholder, filled below
        )
    except Exception:
        raise HTTPException(409, "Already voted")

    # 9. verify Ed25519 sig over encrypted_vote
    try:
        verify_signature(bytes(voter["public_key"]), req.encrypted_vote, req.signature)
    except Exception:
        raise HTTPException(400, "Signature invalid")

    # 10. compute and store merkle leaf
    ts   = datetime.utcnow().isoformat()
    leaf = hash_leaf(nullifier, req.encrypted_vote, ts)
    merkle_tree.insert(leaf)
    # update the leaf in the row we just inserted
    import sqlite3
    conn = sqlite3.connect("voting.db")
    conn.execute("UPDATE votes SET merkle_leaf=?, timestamp=? WHERE nullifier=?",
                 (leaf, ts, nullifier))
    conn.commit()

    # 11-12. run detection + store new root
    detection.verify_chain()
    new_root = merkle_tree.get_root()
    db.insert_root(new_root, db.vote_count())

    # 13. return receipt
    return {"leaf_index": len(merkle_tree.leaves) - 1}