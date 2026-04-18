import base64
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def _b64e(value: bytes) -> str:
    return base64.b64encode(value).decode()


def _b64d(value: str) -> bytes:
    return base64.b64decode(value.encode(), validate=True)


def _derive_wrap_key(shared_secret: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"secure-voting-system election key wrap v1",
    ).derive(shared_secret)


def find_key_file(filename: str) -> Path:
    candidates = []
    env_names = {
        "election_public_key.txt": ["ELECTION_PUBLIC_KEY_PATH"],
        "election_commitments.json": ["ELECTION_COMMITMENTS_PATH"],
    }.get(filename, [])
    for env_name in env_names:
        if os.getenv(env_name):
            candidates.append(Path(os.environ[env_name]))

    here = Path(__file__).resolve()
    candidates.extend([
        Path.cwd() / filename,
        Path.cwd().parent / filename,
        here.parents[2] / filename,
        here.parents[1] / filename,
    ])

    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"{filename} not found")


def load_election_public_key() -> x25519.X25519PublicKey:
    raw_hex = find_key_file("election_public_key.txt").read_text().strip()
    return x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(raw_hex))


def private_key_from_hex(private_hex: str) -> x25519.X25519PrivateKey:
    raw = bytes.fromhex(private_hex)
    if len(raw) != 32:
        raise ValueError("Election private key must be 32 bytes")
    return x25519.X25519PrivateKey.from_private_bytes(raw)


def public_key_hex(private_key: x25519.X25519PrivateKey) -> str:
    public_key = private_key.public_key()
    return public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


def wrap_aes_key_for_db(aes_key: bytes) -> bytes:
    public_key = load_election_public_key()
    ephemeral_private = x25519.X25519PrivateKey.generate()
    ephemeral_public = ephemeral_private.public_key()
    shared_secret = ephemeral_private.exchange(public_key)
    wrap_key = _derive_wrap_key(shared_secret)

    nonce = os.urandom(12)
    ciphertext = AESGCM(wrap_key).encrypt(nonce, aes_key, None)
    ephemeral_public_bytes = ephemeral_public.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    payload = {
        "v": 1,
        "alg": "X25519-HKDF-SHA256-AESGCM",
        "epk": _b64e(ephemeral_public_bytes),
        "nonce": _b64e(nonce),
        "ct": _b64e(ciphertext),
    }
    return json.dumps(payload, separators=(",", ":")).encode()


def unwrap_aes_key_from_db(private_key: x25519.X25519PrivateKey, wrapped: bytes) -> bytes:
    payload = json.loads(wrapped.decode())
    if payload.get("v") != 1:
        raise ValueError("Unsupported wrapped key version")

    ephemeral_public = x25519.X25519PublicKey.from_public_bytes(_b64d(payload["epk"]))
    shared_secret = private_key.exchange(ephemeral_public)
    wrap_key = _derive_wrap_key(shared_secret)
    return AESGCM(wrap_key).decrypt(_b64d(payload["nonce"]), _b64d(payload["ct"]), None)
