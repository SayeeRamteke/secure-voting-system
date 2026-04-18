"""
Pure-Python 3 Shamir Secret Sharing over GF(p).
No external dependencies.
"""
import random
import functools

# A large prime (256-bit Mersenne-like) sufficient for 256-bit hex secrets
_PRIME = 2**521 - 1  # M521 Mersenne prime


def _eval_poly(coeffs, x, prime):
    """Evaluate polynomial at x using Horner's method."""
    result = 0
    for c in reversed(coeffs):
        result = (result * x + c) % prime
    return result


def _mod_inverse(a, prime):
    """Extended Euclidean algorithm to find modular inverse."""
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


def split_secret(secret_hex: str, threshold: int, num_shares: int) -> list[str]:
    """
    Split a hex-encoded secret into num_shares shares.
    Any `threshold` shares can reconstruct it.

    Returns a list of strings formatted as "index-hexvalue".
    """
    secret_int = int(secret_hex, 16)
    if secret_int >= _PRIME:
        raise ValueError("Secret too large for this prime field")

    # Random polynomial of degree (threshold - 1)
    coeffs = [secret_int] + [random.randrange(1, _PRIME) for _ in range(threshold - 1)]

    shares = []
    for i in range(1, num_shares + 1):
        y = _eval_poly(coeffs, i, _PRIME)
        shares.append(f"{i}-{hex(y)[2:]}")  # format: "index-hexvalue"
    return shares


def recover_secret(shares: list[str]) -> str:
    """
    Recover the secret from a list of shares (each "index-hexvalue").
    Returns the secret as a hex string (zero-padded to 64 chars for 256-bit keys).
    """
    points = []
    for s in shares:
        if not isinstance(s, str) or "-" not in s:
            raise ValueError(f"Invalid shard format: {s!r}")
        idx, val = s.split("-", 1)
        if not idx or not val:
            raise ValueError(f"Invalid shard format: {s!r}")
        points.append((int(idx), int(val, 16)))

    # Lagrange interpolation at x=0
    secret = 0
    for i, (xi, yi) in enumerate(points):
        num = yi
        den = 1
        for j, (xj, _) in enumerate(points):
            if i != j:
                num = (num * (-xj)) % _PRIME
                den = (den * (xi - xj)) % _PRIME
        secret = (secret + num * _mod_inverse(den, _PRIME)) % _PRIME

    return hex(secret)[2:].zfill(64)


# ── self-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    key = os.urandom(32).hex()
    print(f"Original : {key}")
    shards = split_secret(key, threshold=2, num_shares=3)
    print(f"Shards   : {shards}")
    recovered = recover_secret([shards[0], shards[2]])  # use shard 1 and 3
    print(f"Recovered: {recovered}")
    assert key == recovered, "MISMATCH — recovery failed!"
    print("Self-test passed ✓")
