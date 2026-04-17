from blake3 import blake3

class MerkleTree:
    def __init__(self):
        self.leaves = []        # raw leaf hashes (hex strings)
        self._root  = None

    def insert(self, leaf_hash: str):
        self.leaves.append(leaf_hash)
        self._root = self._compute_root(self.leaves)

    def get_root(self) -> str:
        if not self.leaves:
            return blake3(b"empty").hexdigest()
        return self._root

    def get_proof(self, index: int) -> list:
        """Return list of {sibling, direction} dicts for leaf at index."""
        if index >= len(self.leaves):
            raise IndexError("leaf index out of range")
        layer = list(self.leaves)
        proof = []
        idx   = index
        while len(layer) > 1:
            if len(layer) % 2 == 1:
                layer.append(layer[-1])     # duplicate last for odd layer
            sibling_idx = idx ^ 1           # XOR flips last bit = partner
            direction   = "right" if idx % 2 == 0 else "left"
            proof.append({"sibling": layer[sibling_idx], "direction": direction})
            layer = [self._hash_pair(layer[i], layer[i+1])
                     for i in range(0, len(layer), 2)]
            idx //= 2
        return proof

    def verify_proof(self, leaf_hash: str, proof: list, root: str) -> bool:
        h = leaf_hash
        for step in proof:
            if step["direction"] == "right":
                h = self._hash_pair(h, step["sibling"])
            else:
                h = self._hash_pair(step["sibling"], h)
        return h == root

    def _compute_root(self, leaves: list) -> str:
        layer = list(leaves)
        while len(layer) > 1:
            if len(layer) % 2 == 1:
                layer.append(layer[-1])
            layer = [self._hash_pair(layer[i], layer[i+1])
                     for i in range(0, len(layer), 2)]
        return layer[0]

    def _hash_pair(self, a: str, b: str) -> str:
        return blake3((a + b).encode()).hexdigest()