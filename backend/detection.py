import db
from crypto.merkle import MerkleTree

class TamperDetected(Exception):
    pass

def verify_chain():
    votes = db.get_all_votes()
    latest_root = db.get_latest_root_record()

    if latest_root:
        expected_count = latest_root["vote_count"]
        if expected_count > len(votes):
            raise TamperDetected(
                f"Stored root references {expected_count} votes, but only {len(votes)} exist")
    else:
        expected_count = len(votes)

    tree = MerkleTree()

    for v in votes[:expected_count]:
        if not v["merkle_leaf"]:
            raise TamperDetected(f"Missing Merkle leaf on vote id={v['id']}")

        tree.insert(v["merkle_leaf"])

    recomputed = tree.get_root()
    if latest_root and recomputed != latest_root["root_hash"]:
        raise TamperDetected(
            f"Merkle root mismatch. Expected {latest_root['root_hash'][:12]}... got {recomputed[:12]}...")
