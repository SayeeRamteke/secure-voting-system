#!/usr/bin/env python3
"""
Generate one election X25519 keypair and split the private key 2-of-3.

Writes:
    election_public_key.txt   -> safe to keep with the server for key wrapping
    election_commitments.json -> public VSS commitments for shard validation
    shard_1.txt, shard_2.txt, shard_3.txt
    election_private_key.txt  -> demo backup only; delete after checking shards
"""
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

from crypto.key_wrap import private_key_from_hex, public_key_hex
from shamir import recover_secret, split_secret_with_commitments, verify_share

OUTPUT_DIR = Path(".")


def main():
    private_key = x25519.X25519PrivateKey.generate()
    private_key_hex = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex()
    public_key = private_key.public_key()
    public_key_hex_value = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()

    shards, commitments = split_secret_with_commitments(
        private_key_hex,
        threshold=2,
        num_shares=3,
    )

    for combo in ((0, 1), (0, 2), (1, 2)):
        recovered_hex = recover_secret([shards[combo[0]], shards[combo[1]]])
        recovered_private = private_key_from_hex(recovered_hex)
        if public_key_hex(recovered_private) != public_key_hex_value:
            print("ERROR: Shamir recovery produced the wrong private key.", file=sys.stderr)
            sys.exit(1)
    print("Shamir recovery verified for all 2-of-3 shard combinations")

    if not all(verify_share(shard, commitments) for shard in shards):
        print("ERROR: VSS commitment verification failed.", file=sys.stderr)
        sys.exit(1)
    print("Feldman VSS commitments verified for all shards")

    for i, shard in enumerate(shards, start=1):
        path = OUTPUT_DIR / f"shard_{i}.txt"
        path.write_text(shard + "\n")
        print(f"Written: {path}")

    (OUTPUT_DIR / "election_public_key.txt").write_text(public_key_hex_value + "\n")
    (OUTPUT_DIR / "election_commitments.json").write_text(
        json.dumps({"threshold": 2, "shares": 3, "commitments": commitments}, indent=2) + "\n"
    )
    (OUTPUT_DIR / "election_private_key.txt").write_text(private_key_hex + "\n")

    print("Written: election_public_key.txt")
    print("Written: election_commitments.json")
    print("Written: election_private_key.txt  (demo backup; delete after shard checks)")


if __name__ == "__main__":
    main()
