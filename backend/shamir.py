"""
Shamir Secret Sharing with Feldman-style public share verification.

Shares keep the existing "index-hexvalue" format. The public commitments are
written separately and let admin.py reject fake or corrupted shards before they
are stored for reveal.
"""
import secrets

# RFC 3526 1536-bit MODP safe prime. We use the subgroup of order q=(p-1)/2.
_GROUP_PRIME = int(
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
    "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
    "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA237327FFFFFFFFFFFFFFFF",
    16,
)
_FIELD_PRIME = (_GROUP_PRIME - 1) // 2
_GENERATOR = 4


def _eval_poly(coeffs, x, prime):
    result = 0
    for c in reversed(coeffs):
        result = (result * x + c) % prime
    return result


def _mod_inverse(a, prime):
    a = a % prime
    if a == 0:
        raise ValueError("No inverse for zero")
    old_r, r = a, prime
    old_s, s = 1, 0
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
    return old_s % prime


def parse_share(share: str) -> tuple[int, int]:
    if not isinstance(share, str) or "-" not in share:
        raise ValueError(f"Invalid shard format: {share!r}")
    idx, val = share.strip().split("-", 1)
    if not idx or not val:
        raise ValueError(f"Invalid shard format: {share!r}")
    return int(idx), int(val, 16)


def split_secret(secret_hex: str, threshold: int, num_shares: int) -> list[str]:
    shares, _ = split_secret_with_commitments(secret_hex, threshold, num_shares)
    return shares


def split_secret_with_commitments(
    secret_hex: str,
    threshold: int,
    num_shares: int,
) -> tuple[list[str], list[str]]:
    secret_int = int(secret_hex, 16)
    if secret_int >= _FIELD_PRIME:
        raise ValueError("Secret too large for this prime field")
    if threshold < 2 or threshold > num_shares:
        raise ValueError("threshold must be between 2 and num_shares")

    coeffs = [secret_int]
    coeffs.extend(secrets.randbelow(_FIELD_PRIME - 1) + 1 for _ in range(threshold - 1))

    commitments = [hex(pow(_GENERATOR, coeff, _GROUP_PRIME))[2:] for coeff in coeffs]
    shares = []
    for i in range(1, num_shares + 1):
        y = _eval_poly(coeffs, i, _FIELD_PRIME)
        shares.append(f"{i}-{hex(y)[2:]}")

    return shares, commitments


def verify_share(share: str, commitments: list[str]) -> bool:
    x, y = parse_share(share)
    left = pow(_GENERATOR, y, _GROUP_PRIME)
    right = 1
    for power, commitment_hex in enumerate(commitments):
        commitment = int(commitment_hex, 16)
        right = (right * pow(commitment, pow(x, power, _FIELD_PRIME), _GROUP_PRIME)) % _GROUP_PRIME
    return left == right


def recover_secret(shares: list[str]) -> str:
    points = [parse_share(s) for s in shares]
    secret = 0
    for i, (xi, yi) in enumerate(points):
        num = yi
        den = 1
        for j, (xj, _) in enumerate(points):
            if i != j:
                num = (num * (-xj)) % _FIELD_PRIME
                den = (den * (xi - xj)) % _FIELD_PRIME
        secret = (secret + num * _mod_inverse(den, _FIELD_PRIME)) % _FIELD_PRIME

    return hex(secret)[2:].zfill(64)


if __name__ == "__main__":
    import os

    key = os.urandom(32).hex()
    print(f"Original : {key}")
    shards, commitments = split_secret_with_commitments(key, threshold=2, num_shares=3)
    print(f"Shards   : {shards}")
    print(f"Verified : {[verify_share(s, commitments) for s in shards]}")
    recovered = recover_secret([shards[0], shards[2]])
    print(f"Recovered: {recovered}")
    assert key == recovered, "MISMATCH: recovery failed"
    assert all(verify_share(s, commitments) for s in shards), "MISMATCH: VSS failed"
    assert not verify_share("1-deadbeef", commitments), "MISMATCH: fake shard accepted"
    print("Self-test passed")
