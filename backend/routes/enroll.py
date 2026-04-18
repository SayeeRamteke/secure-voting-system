from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from webauthn import (generate_registration_options,
                      verify_registration_response)
from blake3 import blake3
import db
import base64
router = APIRouter()

class EnrollBeginReq(BaseModel):
    roll_no: str

class EnrollCompleteReq(BaseModel):
    roll_no: str
    pin: str
    panic_pin: str | None = None
    attestation: dict

@router.post("/register/begin")
async def register_begin(req: EnrollBeginReq, request: Request):
    if not db.roll_exists(req.roll_no):
        raise HTTPException(403, "Roll number not in voter list")

    conn = db.get_conn()
    if conn.execute("SELECT 1 FROM voters WHERE roll_no=?",
                    (req.roll_no,)).fetchone():
        raise HTTPException(409, "Already enrolled")

    opts = generate_registration_options(
        rp_id="localhost",
        rp_name="Voting Demo",
        user_id=req.roll_no.encode(),
        user_name=req.roll_no,
    )

    # store raw challenge bytes in session for verify step
    request.session["reg_challenge"] = base64.b64encode(opts.challenge).decode()
    request.session["reg_roll_no"]   = req.roll_no

    # manually serialize — bytes must be base64 encoded for JSON
    return {
        "challenge": base64.b64encode(opts.challenge).decode(),
        "rp": {"id": opts.rp.id, "name": opts.rp.name},
        "user": {
            "id":          base64.b64encode(opts.user.id).decode(),
            "name":        opts.user.name,
            "displayName": opts.user.display_name,
        },
        "pubKeyCredParams": [
            {"type": p.type if isinstance(p.type, str) else p.type.value, "alg": p.alg if isinstance(p.alg, int) else p.alg.value}
            for p in opts.pub_key_cred_params
        ],
        "timeout":    opts.timeout,
        "attestation": opts.attestation.value,
    }

@router.post("/register/complete")
async def register_complete(req: EnrollCompleteReq, request: Request):
    #challenge = request.session.get("reg_challenge")
    challenge = base64.b64decode(request.session.get("reg_challenge"))
    if not challenge:
        raise HTTPException(400, "No challenge in session")

    try:
        verification = verify_registration_response(
            credential=req.attestation,
            expected_challenge=challenge,
            expected_rp_id="localhost",
            expected_origin="http://localhost:5173",
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(400, f"WebAuthn verification failed: {e}")

    pin = req.pin.strip()
    if not pin.isdigit() or len(pin) < 4 or len(pin) > 12:
        raise HTTPException(400, "PIN must be 4 to 12 digits")

    # The PIN is the voter secret for this demo. Store only its hash.
    voter_secret_hash = blake3(pin.encode()).hexdigest()

    panic_pin_hash = None
    if req.panic_pin and req.panic_pin.strip():
        panic_pin = req.panic_pin.strip()
        if not panic_pin.isdigit() or len(panic_pin) < 4 or len(panic_pin) > 12:
            raise HTTPException(400, "Panic PIN must be 4 to 12 digits")
        if panic_pin == pin:
            raise HTTPException(400, "Panic PIN must be different from voting PIN")
        panic_pin_hash = blake3(panic_pin.encode()).hexdigest()

    roll_no = request.session["reg_roll_no"]
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO voters (roll_no, credential_id, public_key, voter_secret_hash, panic_pin_hash)"
        " VALUES (?,?,?,?,?)",
        (roll_no,
         verification.credential_id,
         verification.credential_public_key,
         voter_secret_hash,
         panic_pin_hash)
    )
    conn.commit()

    return {"message": "PIN registered"}
