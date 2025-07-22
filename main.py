from fastapi import FastAPI
from sqlmodel import SQLModel
from models import Manager, Club, Player, MatchResult, TrainingGround

from auth import router as auth_router
from club import router as club_router
from match import router as match_router

from database import init_db, engine  # ✅ Add engine import here

app = FastAPI()
init_db()

app.include_router(auth_router, prefix="/auth")
app.include_router(club_router, prefix="/club")
app.include_router(match_router, prefix="/match")

# === RUN ON SERVER STARTUP ===
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
