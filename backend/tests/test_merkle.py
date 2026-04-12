from crypto.merkle import MerkleTree

def test_insert_and_root():
    t = MerkleTree()
    t.insert("aaa"); t.insert("bbb")
    assert len(t.get_root()) == 64   # blake3 hex

def test_proof_verifies():
    t = MerkleTree()
    leaves = ["leaf0","leaf1","leaf2","leaf3"]
    for l in leaves: t.insert(l)
    root = t.get_root()
    for i in range(4):
        proof = t.get_proof(i)
        assert t.verify_proof(leaves[i], proof, root)

def test_tamper_detected():
    t = MerkleTree()
    t.insert("leaf0"); t.insert("leaf1")
    root  = t.get_root()
    proof = t.get_proof(0)
    assert not t.verify_proof("TAMPERED", proof, root)