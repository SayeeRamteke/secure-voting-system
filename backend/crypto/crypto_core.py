from blake3 import blake3
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption
)
import os

# ── BLAKE3 ──────────────────────────────────────────
def hash_data(data: bytes) -> str:
    return blake3(data).hexdigest()

def compute_nullifier(voter_secret: str, election_id: str) -> str:
    return blake3((voter_secret + election_id).encode()).hexdigest()

def hash_leaf(nullifier: str, encrypted_vote: bytes, timestamp: str) -> str:
    payload = nullifier.encode() + encrypted_vote + timestamp.encode()
    return blake3(payload).hexdigest()

# ── Ed25519 ─────────────────────────────────────────
def generate_keypair():
    priv = Ed25519PrivateKey.generate()
    pub  = priv.public_key()
    return priv, pub

def serialize_pubkey(pub) -> bytes:
    return pub.public_bytes(Encoding.Raw, PublicFormat.Raw)

def load_pubkey(raw: bytes):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    return Ed25519PublicKey.from_public_bytes(raw)

def sign_vote(private_key, message: bytes) -> bytes:
    return private_key.sign(message)

def verify_signature(public_key_bytes: bytes, message: bytes, signature: bytes):
    # raises InvalidSignature on failure — caller must catch
    pub = load_pubkey(public_key_bytes)
    pub.verify(signature, message)

# ── AES-256-GCM ─────────────────────────────────────
def seal_vote(plaintext: bytes):
    key   = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    ct    = AESGCM(key).encrypt(nonce, plaintext, None)
    return key, nonce, ct           # caller stores key+nonce alongside ct

def open_vote(key: bytes, nonce: bytes, ct: bytes) -> bytes:
    return AESGCM(key).decrypt(nonce, ct, None)