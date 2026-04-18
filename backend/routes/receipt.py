from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from crypto.crypto_core import compute_nullifier, hash_leaf
from crypto.merkle import MerkleTree
from blake3 import blake3
import db

router = APIRouter()

class ReceiptVerifyReq(BaseModel):
    leaf_index: int
    voter_secret: str

def build_tree_from_db():
    tree = MerkleTree()
    for vote in db.get_all_votes():
        if vote["merkle_leaf"]:
            tree.insert(vote["merkle_leaf"])
    return tree

@router.get("/receipt/{leaf_index}")
def get_receipt(leaf_index: int):
    tree = build_tree_from_db()
    if leaf_index >= len(tree.leaves):
        raise HTTPException(404, "Leaf not found")
    proof = tree.get_proof(leaf_index)
    return {
        "leaf_index": leaf_index,
        "leaf_hash":  tree.leaves[leaf_index],
        "proof":      proof,
        "root":       tree.get_root(),
        "vote_count": db.vote_count()
    }

@router.post("/receipt/verify")
def verify_receipt(req: ReceiptVerifyReq):
    if req.leaf_index < 0:
        raise HTTPException(400, "Invalid leaf index")

    vote = db.get_vote_by_leaf_index(req.leaf_index)
    if not vote:
        raise HTTPException(404, "Leaf not found")

    submitted_secret_hash = blake3(req.voter_secret.encode()).hexdigest()
    if vote["receipt_secret_hash"]:
        stable_nullifier = compute_nullifier(submitted_secret_hash, "election_2024")
        if vote["receipt_secret_hash"] != submitted_secret_hash and vote["nullifier"] != stable_nullifier:
            return {"verified": False, "proof_path": []}
    else:
        # Legacy rows from before PIN receipts stored the raw-secret nullifier.
        nullifier = compute_nullifier(req.voter_secret, "election_2024")
        if vote["nullifier"] != nullifier:
            return {"verified": False, "proof_path": []}

    expected_leaf = hash_leaf(
        vote["nullifier"],
        bytes(vote["encrypted_vote"]),
        vote["timestamp"]
    )
    if expected_leaf != vote["merkle_leaf"]:
        return {"verified": False, "proof_path": []}

    tree = build_tree_from_db()
    proof = tree.get_proof(req.leaf_index)
    public_root = db.get_latest_root_record()
    if not public_root:
        return {
            "verified": False,
            "reason": "No public Merkle root has been published yet.",
            "proof_path": [],
            "published_root": None
        }

    verified = tree.verify_proof(expected_leaf, proof, public_root["root_hash"])

    return {
        "verified": verified,
        "ballot_id": req.leaf_index + 1,
        "leaf_hash": expected_leaf,
        "root": public_root["root_hash"],
        "published_root": public_root["root_hash"],
        "total_votes": public_root["vote_count"],
        "published_at": public_root["created_at"],
        "proof_path": [
            {
                "hash": step["sibling"],
                "direction": step["direction"]
            }
            for step in proof
        ]
    }
