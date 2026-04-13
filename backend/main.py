from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import db
from routes import enroll, vote, receipt, health, admin

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

@app.on_event("startup")
def startup():
    db.init_db()
    # rebuild merkle tree from existing votes on restart
    from routes.vote import merkle_tree
    for v in db.get_all_votes():
        merkle_tree.insert(v["merkle_leaf"])

app.include_router(enroll.router)
app.include_router(vote.router)
app.include_router(receipt.router)
app.include_router(health.router)
app.include_router(admin.router)

# run: uvicorn main:app --reload --port 8000



