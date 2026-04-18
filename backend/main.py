import os
from dotenv import load_dotenv

# This looks for the .env file in the root
load_dotenv() 

# Now you can access it anywhere in your code
token = os.getenv("ADMIN_SECRET_TOKEN")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from backend import db
from backend.routes import enroll, vote, receipt, health, admin

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="demo-secret-change-in-prod",
    same_site="lax",
    https_only=False,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True, 
)

app.include_router(enroll.router)
app.include_router(vote.router)
app.include_router(receipt.router)
app.include_router(health.router)
app.include_router(admin.router)

import json
from pathlib import Path

@app.on_event("startup")
def startup():
    db.init_db()
    
    # NEW: Automatically sync VSS commitments from file to DB
    commitments_path = Path("election_commitments.json")
    if commitments_path.exists():
        with open(commitments_path, "r") as f:
            data = json.load(f)
            # This ensures your admin route has the "satellite photo" to check shards
            db.save_commitments(json.dumps(data["commitments"]))
            print("✓ Election commitments synced to database.")

    # Rebuild Merkle tree (Existing logic)
    from backend.routes.vote import merkle_tree
    for v in db.get_all_votes():
        # Make sure your db.get_all_votes() is updated to handle the new schema
        merkle_tree.insert(v["merkle_leaf"])

# run: uvicorn main:app --reload --port 8000



