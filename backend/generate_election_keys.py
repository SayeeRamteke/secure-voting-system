#!/usr/bin/env python3
"""
generate_election_keys.py — Run ONCE before the election, offline if possible.

Usage:
    python generate_election_keys.py

Writes:
    shard_1.txt  →  hand to Trustee 1
    shard_2.txt  →  hand to Trustee 2
    shard_3.txt  →  hand to Trustee 3

    election_key.txt  →  store in a hardware security module or sealed
                          envelope; destroy after confirming shards work.

The key is split 2-of-3: any two trustees can reconstruct it.
Never store all three shards together.
"""

import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
"""from secretsharing import PlaintextToHexSecretSharer as SS"""
from shamir import split_secret, recover_secret

OUTPUT_DIR = Path(".")


def main():
    # ── Generate key ─────────────────────────────────────────────────────────
    election_key = AESGCM.generate_key(bit_length=256)   # 32 random bytes
    election_key_hex = election_key.hex()                 # 64 hex chars

    # Guard: secretsharing can silently lose leading zeros on short keys.
    # blake3/AESGCM keys are always 32 bytes so this shouldn't happen,
    # but assert defensively.
    assert len(election_key_hex) == 64, "Key hex must be 64 chars"

    # ── Split into 3 shards, threshold = 2 ───────────────────────────────────
    shards = split_secret(election_key_hex, threshold=2, num_shares=3)
    assert len(shards) == 3

    # ── Verify round-trip BEFORE writing anything ─────────────────────────────
    recovered_hex = recover_secret([shards[0], shards[1]])
    recovered_key = bytes.fromhex(recovered_hex)
    if recovered_key != election_key:
        print("ERROR: Shamir round-trip verification failed. Key NOT written.", file=sys.stderr)
        sys.exit(1)
    print("✓ Shamir round-trip verified (shards 1+2 → original key)")

    recovered_hex2 = recover_secret([shards[1], shards[2]])
    if bytes.fromhex(recovered_hex2) != election_key:
        print("ERROR: Shamir round-trip verification failed (shards 2+3). Key NOT written.", file=sys.stderr)
        sys.exit(1)
    print("✓ Shamir round-trip verified (shards 2+3 → original key)")

    # ── Write shard files ─────────────────────────────────────────────────────
    for i, shard in enumerate(shards, start=1):
        path = OUTPUT_DIR / f"shard_{i}.txt"
        path.write_text(shard + "\n")
        print(f"  Written: {path}  →  give to Trustee {i}")

    # ── Write key file (keep offline/destroy after confirming shards) ─────────
    key_path = OUTPUT_DIR / "election_key.txt"
    key_path.write_text(election_key_hex + "\n")
    print(f"\n  Written: {key_path}")
    print("  ⚠️  Store this in a sealed envelope or HSM.")
    print("  ⚠️  Delete after confirming the three shards work independently.\n")

    print("Done. Distribute shard files to trustees — never send two shards to the same person.")


if __name__ == "__main__":
    main()