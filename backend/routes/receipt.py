from fastapi import APIRouter, HTTPException
from routes.vote import merkle_tree
import db

router = APIRouter()

@router.get("/receipt/{leaf_index}")
def get_receipt(leaf_index: int):
    if leaf_index >= len(merkle_tree.leaves):
        raise HTTPException(404, "Leaf not found")
    proof = merkle_tree.get_proof(leaf_index)
    return {
        "leaf_index": leaf_index,
        "leaf_hash":  merkle_tree.leaves[leaf_index],
        "proof":      proof,
        "root":       merkle_tree.get_root(),
        "vote_count": db.vote_count()
    }