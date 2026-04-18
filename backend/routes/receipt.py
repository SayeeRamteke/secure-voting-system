from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from crypto.crypto_core import compute_nullifier, hash_leaf
from crypto.merkle import MerkleTree
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
    root = db.get_latest_root() or tree.get_root()
    verified = tree.verify_proof(expected_leaf, proof, root)

    return {
        "verified": verified,
        "leaf_hash": expected_leaf,
        "root": root,
        "proof_path": [
            {
                "hash": step["sibling"],
                "direction": step["direction"]
            }
            for step in proof
        ]
    }
