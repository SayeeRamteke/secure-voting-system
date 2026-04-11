from fastapi import FastAPI
from db import init_db

# create app (THIS is what uvicorn needs)
app = FastAPI()

# initialize DB on startup
init_db()

@app.get("/")
def root():
    return {"status": "backend running"}