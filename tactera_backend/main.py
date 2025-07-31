from sqlmodel import SQLModel, Session
from fastapi import FastAPI

# --- Models ---
from tactera_backend.models.player_stat_model import PlayerStat
from tactera_backend.models.club_model import Club
from tactera_backend.models.training_model import TrainingGround
from tactera_backend.models.manager_model import Manager
from tactera_backend.models.player_model import Player
from tactera_backend.models.match_model import Match

# --- Core / Routes / Services ---
from tactera_backend.core.auth import router as auth_router
from tactera_backend.routes.club_routes import router as club_router
from tactera_backend.services.match import router as match_router
from tactera_backend.routes.player_routes import router as player_router
from tactera_backend.seed.seed_xp_levels import safe_seed_stat_levels
from tactera_backend.routes.league_routes import router as league_router
from tactera_backend.core.database import init_db, engine
from tactera_backend.services.training import router as training_router

# ✅ Create FastAPI app
app = FastAPI()

# ✅ Initialize DB and create tables
init_db()
SQLModel.metadata.create_all(engine)

# ✅ Seed XP levels
safe_seed_stat_levels()

# ✅ Include Routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(club_router, prefix="/clubs", tags=["Clubs"])
app.include_router(player_router, prefix="/players", tags=["Players"])
app.include_router(match_router, prefix="/matches", tags=["Matches"])
app.include_router(league_router, prefix="/leagues", tags=["Leagues"])
app.include_router(training_router, prefix="/training", tags=["Training"])
