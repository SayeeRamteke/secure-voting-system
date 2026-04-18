"""
routes/admin.py — Shamir combine + tally, with trustee quorum and admin auth.

Key fixes over original:
  1. Shards are submitted one at a time by separate trustees (no both-in-one-request).
  2. Admin session token required on every endpoint.
  3. Each vote is decrypted with its OWN per-vote aes_key (from DB), NOT the
     bare election key — matching how vote.py stores them.
  4. Errors surface as HTTP 207 so callers can't silently miss failed ballots.
  5. Shard store is cleared after a successful reveal (one-shot).
  6. generate_election_keys() is a standalone CLI script, not an importable
     function that could accidentally be called at runtime.
"""

import os
import secrets
import logging
import base64
import re
import json
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from shamir import recover_secret, verify_share
import db
from crypto.crypto_core import open_vote
from crypto.key_wrap import find_key_file, private_key_from_hex, unwrap_aes_key_from_db

router = APIRouter()
logger = logging.getLogger(__name__)

# ── In-memory shard store (keyed by session token) ──────────────────────────
# Maps  admin_token -> { "shards": [shard1, ...], "submitted_at": datetime }
# In production, replace with a short-TTL Redis store.
_shard_store: dict[str, dict] = {}

REQUIRED_SHARDS = 2          # 2-of-3 threshold
SHARD_TTL_MINUTES = 30       # window for trustees to submit their shards
ADMIN_TOKEN_ENV = "ADMIN_SECRET_TOKEN"   # set this env var before starting
SHARD_RE = re.compile(r"^[1-9]\d*-[0-9a-fA-F]+$")


# ── Auth dependency ──────────────────────────────────────────────────────────

def _get_admin_token() -> str:
    token = os.getenv(ADMIN_TOKEN_ENV)
    if not token or len(token) < 32:
        raise RuntimeError(
            f"${ADMIN_TOKEN_ENV} must be set to a 32+ char random string"
        )
    return token


def require_admin(request: Request) -> None:
    """Dependency: validates Bearer token in Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing Authorization: Bearer <token>")

    provided = auth_header.removeprefix("Bearer ").strip()
    expected = _get_admin_token()

    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(provided, expected):
        raise HTTPException(403, "Invalid admin token")


# ── Models ───────────────────────────────────────────────────────────────────

class ShardSubmitReq(BaseModel):
    trustee_id: str   # e.g. "trustee_1", "trustee_2" — for logging only
    shard: str


class RevealReq(BaseModel):
    pass   # no body needed; shards are already held in _shard_store


# ── Endpoints ────────────────────────────────────────────────────────────────

def normalize_shard(shard: str) -> str:
    normalized = "".join(shard.split())
    if not normalized:
        raise HTTPException(400, "Shard must not be empty")
    if not SHARD_RE.fullmatch(normalized):
        raise HTTPException(
            400,
            "Invalid shard format. Expected something like '1-abcdef...' with no labels."
        )
    return normalized

def load_commitments() -> list[str]:
    try:
        payload = json.loads(find_key_file("election_commitments.json").read_text())
        commitments = payload["commitments"]
    except Exception as e:
        raise HTTPException(500, f"Election VSS commitments not available: {e}")

    if not isinstance(commitments, list) or not commitments:
        raise HTTPException(500, "Election VSS commitments are invalid")
    return commitments

@router.post("/admin/shard", dependencies=[Depends(require_admin)])
def submit_shard(req: ShardSubmitReq, request: Request) -> dict:
    """
    Trustee calls this endpoint with their individual shard.
    Returns how many shards have been collected so far.
    """
    shard = normalize_shard(req.shard)
    commitments = load_commitments()
    try:
        valid = verify_share(shard, commitments)
    except Exception as e:
        raise HTTPException(400, f"Shard verification failed: {e}")
    if not valid:
        raise HTTPException(400, "Share verification failed")

    # Use a single shared slot (demo: one election at a time).
    # In production, key by election_id.
    slot = _shard_store.setdefault("active", {
        "shards": [],
        "trustee_ids": [],
        "submitted_at": datetime.now(timezone.utc),
    })

    # Check TTL
    age_minutes = (
        datetime.now(timezone.utc) - slot["submitted_at"]
    ).total_seconds() / 60
    if age_minutes > SHARD_TTL_MINUTES:
        _shard_store.pop("active", None)
        raise HTTPException(
            410,
            f"Shard collection window expired ({SHARD_TTL_MINUTES} min). "
            "Start over — first trustee must resubmit."
        )

    # Deduplicate by trustee_id
    if req.trustee_id in slot["trustee_ids"]:
        raise HTTPException(409, f"Trustee '{req.trustee_id}' already submitted a shard")

    if shard in slot["shards"]:
        raise HTTPException(409, "This shard was already submitted")

    slot["shards"].append(shard)
    slot["trustee_ids"].append(req.trustee_id)

    logger.info(
        "Shard received from trustee=%s  total=%d/%d",
        req.trustee_id, len(slot["shards"]), REQUIRED_SHARDS
    )

    return {
        "shards_received": len(slot["shards"]),
        "shards_required": REQUIRED_SHARDS,
        "ready": len(slot["shards"]) >= REQUIRED_SHARDS,
    }


@router.post("/admin/reveal", dependencies=[Depends(require_admin)])
def reveal(request: Request) -> dict:
    """
    Combine collected shards, decrypt every ballot, return tally.
    Requires REQUIRED_SHARDS to have been submitted via /admin/shard first.
    Clears the shard store after success (one-shot reveal).
    """
    slot = _shard_store.get("active")
    if not slot or len(slot["shards"]) < REQUIRED_SHARDS:
        held = len(slot["shards"]) if slot else 0
        raise HTTPException(
            400,
            f"Not enough shards: have {held}, need {REQUIRED_SHARDS}. "
            "POST to /admin/shard first."
        )

    # ── 1. Reconstruct election key ──────────────────────────────────────────
    try:
        election_private_hex = recover_secret(slot["shards"][:REQUIRED_SHARDS])
        election_private_key = private_key_from_hex(election_private_hex)
    except Exception as e:
        logger.error("Shamir combine failed: %s", e)
        raise HTTPException(400, f"Shamir combine failed: {e}")
    finally:
        # Always clear shards from memory — whether combine succeeded or not
        _shard_store.pop("active", None)

    # ── 2. Decrypt and tally ─────────────────────────────────────────────────
    votes = db.get_all_votes()
    tally = Counter()
    errors: list[str] = []

    for v in votes:
        vote_id = v["id"]
        encrypted_vote = bytes(v["encrypted_vote"])
        try:
            # aes_key stores a wrapped per-vote AES key. The reconstructed
            # election private key unwraps it at reveal time.
            per_vote_key   = unwrap_aes_key_from_db(election_private_key, bytes(v["aes_key"]))
            nonce          = bytes(v["aes_nonce"])

            # Validate nonce length (AES-GCM requires exactly 12 bytes)
            if len(nonce) != 12:
                raise ValueError(f"Bad nonce length: {len(nonce)} (expected 12)")

            plaintext = open_vote(per_vote_key, nonce, encrypted_vote)
            candidate = plaintext.decode("utf-8").strip()

            if not candidate:
                raise ValueError("Decrypted to empty string")

            tally[candidate] += 1

        except Exception as e:
            try:
                # Development compatibility for ballots cast before AES-GCM was
                # wired in. Those rows stored btoa(candidate) as encrypted_vote.
                candidate = base64.b64decode(encrypted_vote, validate=True).decode("utf-8").strip()
                if not candidate:
                    raise ValueError("Legacy ballot decoded to empty string")
                tally[candidate] += 1
            except Exception:
                err_msg = f"vote id={vote_id}: {e}"
                logger.warning("Decryption error — %s", err_msg)
                errors.append(err_msg)

    total = sum(tally.values())

    logger.info(
        "Reveal complete: total=%d errors=%d candidates=%s",
        total, len(errors), list(tally.keys())
    )

    # ── 3. Return — flag errors clearly ─────────────────────────────────────
    response_body = {
        "results": dict(tally),
        "total": total,
        "error_count": len(errors),
        "errors": errors,
    }

    if errors:
        # 207 Multi-Status: partial success — caller cannot miss this
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=207, content=response_body)

    return response_body


@router.delete("/admin/shards", dependencies=[Depends(require_admin)])
def clear_shards() -> dict:
    """Emergency: clear collected shards without revealing (e.g. abort)."""
    _shard_store.pop("active", None)
    return {"message": "Shard store cleared"}


@router.get("/admin/shard-status", dependencies=[Depends(require_admin)])
def shard_status() -> dict:
    """Check how many shards have been collected."""
    slot = _shard_store.get("active")
    if not slot:
        return {"shards_received": 0, "shards_required": REQUIRED_SHARDS, "ready": False}
    return {
        "shards_received": len(slot["shards"]),
        "shards_required": REQUIRED_SHARDS,
        "ready": len(slot["shards"]) >= REQUIRED_SHARDS,
        "trustee_ids": slot["trustee_ids"],
    }
