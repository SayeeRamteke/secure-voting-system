from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from blake3 import blake3
from datetime import datetime
import base64
import db, detection
from crypto.crypto_core import compute_nullifier, hash_leaf
from crypto.key_wrap import wrap_aes_key_for_db
from crypto.merkle import MerkleTree

router = APIRouter()
merkle_tree = MerkleTree()   # in-memory; rebuilt from DB on startup (see main.py)

def ensure_current_root():
    votes = db.get_all_votes()
    latest_root = db.get_latest_root_record()
    if latest_root and latest_root["vote_count"] == len(votes):
        return latest_root["root_hash"]

    tree = MerkleTree()
    for vote in votes:
        if not vote["merkle_leaf"]:
            raise detection.TamperDetected(f"Missing Merkle leaf on vote id={vote['id']}")
        tree.insert(vote["merkle_leaf"])

    root = tree.get_root()
    db.insert_root(root, len(votes))
    return root

def decode_client_bytes(value: bytes) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except Exception:
        return value

class VoteCompleteReq(BaseModel):
    credential_id: str
    voter_secret: str
    encrypted_vote: bytes   # AES-256-GCM sealed, from client
    aes_key: bytes          # raw per-vote AES key from client; wrapped before DB storage
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

    # 3. verify BLAKE3(PIN) == stored hash
    if blake3(req.voter_secret.encode()).hexdigest() != voter["voter_secret_hash"]:
        raise HTTPException(403, "PIN mismatch")

    # 4. compute nullifier
    nullifier = compute_nullifier(req.voter_secret, "election_2024")
    encrypted_vote = decode_client_bytes(req.encrypted_vote)
    try:
        aes_key = wrap_aes_key_for_db(decode_client_bytes(req.aes_key))
    except Exception as e:
        raise HTTPException(500, f"Election public key wrapping failed: {e}")
    aes_nonce = decode_client_bytes(req.aes_nonce)
    signature = decode_client_bytes(req.signature)

    # 5. atomic insert — UNIQUE(nullifier) rejects double vote
    try:
        db.insert_vote(
            nullifier=nullifier,
            encrypted_vote=encrypted_vote,
            aes_key=aes_key,
            aes_nonce=aes_nonce,
            signature=signature,
            leaf=""
        )
    except Exception:
        existing_vote = db.get_vote_by_nullifier(nullifier)
        leaf_index = db.get_vote_leaf_index(nullifier)
        if existing_vote and existing_vote["merkle_leaf"] and leaf_index is not None:
            try:
                current_root = ensure_current_root()
            except detection.TamperDetected as e:
                raise HTTPException(500, f"Tamper detected: {e}")
            return {
                "leaf_index": leaf_index,
                "merkle_leaf": existing_vote["merkle_leaf"],
                "merkle_root": current_root,
                "already_voted": True
            }
        raise HTTPException(409, "Already voted")

    # 6. compute and store merkle leaf
    ts = datetime.utcnow().isoformat()
    leaf = hash_leaf(nullifier, encrypted_vote, ts)
    merkle_tree.insert(leaf)

    db.update_vote_leaf_timestamp(nullifier, leaf, ts)

    # 7. run detection + store new root
    try:
        detection.verify_chain()
    except detection.TamperDetected as e:
        raise HTTPException(500, f"Tamper detected: {e}")

    new_root = ensure_current_root()

    return {
        "leaf_index": len(merkle_tree.leaves) - 1,
        "merkle_leaf": leaf,
        "merkle_root": new_root,
        "already_voted": False
    }
