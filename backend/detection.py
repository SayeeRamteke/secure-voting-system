from crypto.merkle import MerkleTree
from crypto.crypto_core import verify_signature
from cryptography.exceptions import InvalidSignature
import db

class TamperDetected(Exception):
    pass

def verify_chain():
    votes = db.get_all_votes()
    tree  = MerkleTree()

    for v in votes:
        # check 1: re-verify Ed25519 signature
        try:
            verify_signature(bytes(v["public_key"]),    # stored at enroll time
                             bytes(v["encrypted_vote"]),
                             bytes(v["signature"]))
        except InvalidSignature:
            raise TamperDetected(
                f"Sig invalid on vote id={v['id']}, leaf={v['merkle_leaf'][:8]}…")

        tree.insert(v["merkle_leaf"])

    # check 2: recomputed root vs stored root
    recomputed = tree.get_root()
    stored     = db.get_latest_root()
    if stored and recomputed != stored:
        raise TamperDetected(
            f"Merkle root mismatch. Expected {stored[:12]}… got {recomputed[:12]}…")