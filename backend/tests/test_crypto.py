from crypto.crypto_core import *

def test_nullifier_deterministic():
    a = compute_nullifier("secret", "election1")
    b = compute_nullifier("secret", "election1")
    assert a == b

def test_nullifier_unique():
    assert compute_nullifier("s1","e1") != compute_nullifier("s2","e1")

def test_ed25519_roundtrip():
    priv, pub = generate_keypair()
    msg = b"vote:candidateA"
    sig = sign_vote(priv, msg)
    verify_signature(serialize_pubkey(pub), msg, sig)  # must not raise

def test_ed25519_tamper():
    from cryptography.exceptions import InvalidSignature
    import pytest
    priv, pub = generate_keypair()
    sig = sign_vote(priv, b"original")
    with pytest.raises(InvalidSignature):
        verify_signature(serialize_pubkey(pub), b"tampered", sig)

def test_aes_roundtrip():
    key, nonce, ct = seal_vote(b"candidateB")
    assert open_vote(key, nonce, ct) == b"candidateB"

def test_aes_wrong_key():
    import pytest
    key, nonce, ct = seal_vote(b"vote")
    wrong = AESGCM.generate_key(bit_length=256)
    with pytest.raises(Exception):
        open_vote(wrong, nonce, ct)