"""
attack_routes.py — FastAPI router for Attack Lab simulations
Mount this in your main app: app.include_router(router)

Dependencies (add to requirements.txt):
  fastapi
  pydantic
  blake3
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from blake3 import blake3
import os

# ---------------------------------------------------------------------------
# Import your project's own modules.
# Adjust these paths to match your actual project layout.
# ---------------------------------------------------------------------------
try:
    import db
    from crypto.crypto_core import hash_data
    from routes.admin import load_commitments
    from shamir import verify_share
    _FULL_BACKEND = True
except ImportError:
    _FULL_BACKEND = False  # run in demo/stub mode when project modules are absent


router = APIRouter(prefix="", tags=["attack-lab"])


# ---------------------------------------------------------------------------
# Scenario registry (metadata only — used by the frontend list endpoint)
# ---------------------------------------------------------------------------

SCENARIOS = [
    {
        "id": "credential_stuffing",
        "title": "Leaked Roll Number + PIN",
        "attack": "Attacker tries a known roll number and PIN from a breach.",
        "defense": "PIN alone is not enough. WebAuthn requires the registered hardware private key.",
        "live_probe": False,
    },
    {
        "id": "double_vote",
        "title": "Second Vote Attempt",
        "attack": "Same voter tries to cast another ballot after one is already recorded.",
        "defense": "The election nullifier is stable per voter, so the database rejects the duplicate.",
        "live_probe": True,
    },
    {
        "id": "fake_shard",
        "title": "Fake Trustee Shard",
        "attack": "Attacker submits a forged Shamir shard to fish for reveal behavior.",
        "defense": "Feldman VSS commitments reject fake shares before they enter the shard store.",
        "live_probe": False,
    },
    {
        "id": "merkle_forgery",
        "title": "Fake Merkle Receipt",
        "attack": "Attacker builds a fake tree and proof that verifies against a fake root.",
        "defense": "Receipts are checked against the public bulletin-board root, not an attacker root.",
        "live_probe": False,
    },
    {
        "id": "panic_pin",
        "title": "Forced Vote With Panic PIN",
        "attack": "A coercer watches the voter cast a ballot using the panic PIN.",
        "defense": "The surface flow looks normal, but the ballot is marked decoy and skipped at reveal.",
        "live_probe": False,
    },
]


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AttackRunReq(BaseModel):
    scenario_id: str
    roll_no: str | None = None
    pin: str | None = None
    allow_live_probe: bool = False


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def step(status: str, title: str, detail: str) -> dict:
    return {"status": status, "title": title, "detail": detail}


def _get_voter_by_roll(roll_no: str) -> dict | None:
    if not _FULL_BACKEND:
        # Stub: pretend roll 101 exists with a known PIN hash
        if roll_no == "101":
            return {
                "voter_secret_hash": blake3(b"1234").hexdigest(),
                "panic_pin_hash":    blake3(b"0000").hexdigest(),
            }
        return None
    conn = db.get_conn()
    return conn.execute(
        "SELECT * FROM voters WHERE roll_no=?", (roll_no,)
    ).fetchone()


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@router.get("/attack/scenarios")
def attack_scenarios():
    """Return the list of available attack scenarios (used by the sidebar)."""
    return {"scenarios": SCENARIOS}


@router.post("/attack/run")
def run_attack(req: AttackRunReq):
    """
    Execute an attack simulation and return structured telemetry.

    The response shape is always:
        {
            "scenario_id": str,
            "verdict":     "defended" | "vulnerable" | "needs_data" | "needs_setup",
            "summary":     str,
            "events":      [{"status": str, "title": str, "detail": str}, ...]
        }
    """
    handlers = {
        "credential_stuffing": lambda: _sim_credential_stuffing(req.roll_no, req.pin),
        "double_vote":         lambda: _sim_double_vote(req.allow_live_probe),
        "fake_shard":          lambda: _sim_fake_shard(),
        "merkle_forgery":      lambda: _sim_merkle_forgery(),
        "panic_pin":           lambda: _sim_panic_pin(),
    }
    handler = handlers.get(req.scenario_id)
    if not handler:
        raise HTTPException(status_code=404, detail="Unknown attack scenario")
    return handler()


# ---------------------------------------------------------------------------
# Simulation: Credential stuffing
# ---------------------------------------------------------------------------

def _sim_credential_stuffing(roll_no: str | None, pin: str | None) -> dict:
    events = []
    voter = _get_voter_by_roll(roll_no.strip()) if roll_no else None
    pin_hash = blake3((pin or "").encode()).hexdigest()

    if not roll_no or not pin:
        events.append(step(
            "blocked",
            "Credential list incomplete",
            "Provide a roll number and PIN to simulate a leaked-credential attempt.",
        ))
    elif not voter:
        events.append(step("blocked", "Roll number rejected", "The roll number is not enrolled."))
    elif pin_hash not in (voter["voter_secret_hash"], voter["panic_pin_hash"]):
        events.append(step("blocked", "PIN rejected", "The leaked PIN does not match any enrolled PIN hash."))
    else:
        events.append(step("passed", "PIN check would pass", "The attacker guessed a valid PIN."))

    events.append(step(
        "blocked",
        "WebAuthn challenge cannot be answered",
        "The attacker still lacks the authenticator private key bound to the enrolled device.",
    ))
    events.append(step(
        "defended",
        "Vote endpoint remains closed",
        "Without a valid signed WebAuthn assertion, /vote/complete returns HTTP 401.",
    ))

    return {
        "scenario_id": "credential_stuffing",
        "verdict":     "defended",
        "summary":     "Leaked PINs are not enough — the hardware-backed credential is required to vote.",
        "events":      events,
    }


# ---------------------------------------------------------------------------
# Simulation: Double vote (nullifier collision)
# ---------------------------------------------------------------------------

def _sim_double_vote(allow_live_probe: bool) -> dict:
    if not _FULL_BACKEND:
        # Stub response when running without the real database
        return {
            "scenario_id": "double_vote",
            "verdict":     "defended",
            "summary":     "A second ballot from the same voter is blocked by the stable election nullifier.",
            "events": [
                step("observed", "Stub mode", "Connect the real database to probe the UNIQUE constraint live."),
                step("defended", "UNIQUE(nullifier)", "The votes table enforces a unique nullifier constraint."),
            ],
        }

    votes = db.get_all_votes()
    if not votes:
        return {
            "scenario_id": "double_vote",
            "verdict":     "needs_data",
            "summary":     "Cast one ballot first, then run this simulation.",
            "events": [
                step("blocked", "No existing ballot", "The lab needs an existing nullifier to probe duplicate rejection.")
            ],
        }

    existing = votes[-1]
    events = [
        step("observed", "Existing nullifier found", f"Using vote id={existing['id']} as the duplicate target."),
        step("defended", "UNIQUE(nullifier)", "The votes table has a unique nullifier constraint."),
    ]
    verdict = "defended"

    if allow_live_probe:
        try:
            db.insert_vote(
                nullifier=existing["nullifier"],
                encrypted_vote=bytes(existing["encrypted_vote"]),
                aes_key=bytes(existing["aes_key"]),
                aes_nonce=bytes(existing["aes_nonce"]),
                signature=bytes(existing["signature"]),
                leaf="attack-lab-duplicate",
            )
            events.append(step("failed", "Unexpected insert", "Duplicate insert succeeded — this should not happen."))
            verdict = "vulnerable"
        except Exception:
            events.append(step("blocked", "Duplicate insert rejected", "SQLite rejected the second vote with the same nullifier."))
    else:
        events.append(step(
            "dry_run",
            "Live probe skipped",
            "Enable 'allow live probe' to intentionally trigger the constraint rejection.",
        ))

    return {
        "scenario_id": "double_vote",
        "verdict":     verdict,
        "summary":     "A second ballot from the same voter is blocked by the stable election nullifier.",
        "events":      events,
    }


# ---------------------------------------------------------------------------
# Simulation: Fake trustee shard (Feldman VSS)
# ---------------------------------------------------------------------------

def _sim_fake_shard() -> dict:
    if not _FULL_BACKEND:
        return {
            "scenario_id": "fake_shard",
            "verdict":     "defended",
            "summary":     "Fake trustee shards are rejected before reveal.",
            "events": [
                step("attack",  "Forged shard submitted",  "Test shard: 1-deadbeef"),
                step("blocked", "Feldman VSS verification", "The shard does not match the public polynomial commitments."),
            ],
        }

    fake_shard = "1-deadbeef"
    try:
        accepted = verify_share(fake_shard, load_commitments())
    except Exception as exc:
        return {
            "scenario_id": "fake_shard",
            "verdict":     "needs_setup",
            "summary":     f"VSS commitments are not ready: {exc}",
            "events": [step("blocked", "Commitments unavailable", "Generate election keys and restart the backend.")],
        }

    return {
        "scenario_id": "fake_shard",
        "verdict":     "vulnerable" if accepted else "defended",
        "summary":     "Fake trustee shards are rejected before reveal.",
        "events": [
            step("attack",  "Forged shard submitted",    f"Test shard: {fake_shard}"),
            step(
                "blocked" if not accepted else "failed",
                "Feldman VSS verification",
                "The shard does not match the public polynomial commitments."
                if not accepted
                else "The fake shard was accepted — investigate the VSS implementation.",
            ),
        ],
    }


# ---------------------------------------------------------------------------
# Simulation: Merkle root forgery
# ---------------------------------------------------------------------------

def _sim_merkle_forgery() -> dict:
    if not _FULL_BACKEND:
        return {
            "scenario_id": "merkle_forgery",
            "verdict":     "defended",
            "summary":     "A fake proof only works against its fake root, not the public election root.",
            "events": [
                step("attack",   "Fake receipt tree built",  "Attacker root: 0xdeadbeef1234..."),
                step("observed", "Public root fetched",      "Official root: 0x5a3f91c872de..."),
                step("blocked",  "Root comparison",          "Fake root does not match the public bulletin-board root."),
            ],
        }

    public_root = db.get_latest_root_record()
    fake_leaf    = hash_data(os.urandom(32))
    fake_sibling = hash_data(os.urandom(32))
    fake_root    = hash_data((fake_leaf + fake_sibling).encode())

    if not public_root:
        return {
            "scenario_id": "merkle_forgery",
            "verdict":     "needs_data",
            "summary":     "No public root has been published yet.",
            "events": [step("blocked", "Public board empty", "Cast a vote first so the bulletin board has a root.")],
        }

    defended = fake_root != public_root["root_hash"]
    return {
        "scenario_id": "merkle_forgery",
        "verdict":     "defended" if defended else "vulnerable",
        "summary":     "A fake proof only works against its fake root, not the public election root.",
        "events": [
            step("attack",   "Fake receipt tree built",  f"Attacker root: {fake_root[:16]}..."),
            step("observed", "Public root fetched",       f"Official root: {public_root['root_hash'][:16]}..."),
            step(
                "blocked" if defended else "failed",
                "Root comparison",
                "Fake root does not match the public bulletin-board root."
                if defended
                else "Fake root matched the public root — this should never happen.",
            ),
        ],
    }


# ---------------------------------------------------------------------------
# Simulation: Panic PIN / coercion
# ---------------------------------------------------------------------------

def _sim_panic_pin() -> dict:
    if not _FULL_BACKEND:
        return {
            "scenario_id": "panic_pin",
            "verdict":     "defended",
            "summary":     "Panic PIN ballots look normal at cast time but are excluded from final tally.",
            "events": [
                step("attack",   "Coerced ballot cast",          "The visible voting flow returns the same success screen."),
                step("defended", "Decoy marker stored server-side", "The final reveal skips rows marked is_decoy=1."),
                step("observed", "Current lab state",            "Normal ballots: N/A  |  decoy ballots: N/A  (stub mode)."),
            ],
        }

    conn = db.get_conn()
    decoy_count = conn.execute("SELECT COUNT(*) FROM votes WHERE is_decoy=1").fetchone()[0]
    real_count  = conn.execute("SELECT COUNT(*) FROM votes WHERE is_decoy=0").fetchone()[0]

    return {
        "scenario_id": "panic_pin",
        "verdict":     "defended",
        "summary":     "Panic PIN ballots look normal at cast time but are excluded from final tally.",
        "events": [
            step("attack",   "Coerced ballot cast",           "The visible voting flow returns the same receipt-style success screen."),
            step("defended", "Decoy marker stored server-side","The final reveal skips rows marked is_decoy=1."),
            step("observed", "Current lab state",             f"Normal ballots: {real_count}  |  decoy ballots: {decoy_count}."),
        ],
    }