from sqlmodel import SQLModel, select, Session
from fastapi import FastAPI

# --- Models ---
from tactera_backend.models.club_model import Club
from tactera_backend.models.country_model import Country
from tactera_backend.models.league_model import League
from tactera_backend.models.manager_model import Manager
from tactera_backend.models.match_model import Match
from tactera_backend.models.player_model import Player
from tactera_backend.models.player_stat_model import PlayerStat
from tactera_backend.models.season_model import SeasonState
from tactera_backend.models.stadium_model import Stadium
from tactera_backend.models.stat_level_requirement_model import StatLevelRequirement
from tactera_backend.models.training_model import TrainingGround, TrainingHistory, TrainingHistoryStat

# --- Core / Routes / Services ---
from tactera_backend.core.auth import router as auth_router
from tactera_backend.routes.club_routes import router as club_router
from tactera_backend.services.match import router as match_router
from tactera_backend.routes.player_routes import router as player_router
from tactera_backend.routes.league_routes import router as league_router
from tactera_backend.core.database import init_db, engine
from tactera_backend.services.training import router as training_router
from tactera_backend.core.database import init_db, engine, sync_engine   # ✅ import sync_engine too


# --- Seeds ---
from tactera_backend.seed.seed_all import seed_all

# ✅ Create FastAPI app
app = FastAPI()

# ✅ Initialize DB + Seed on Startup
@app.on_event("startup")
async def on_startup():
    # Initialize DB tables
    await init_db()

    # Resolve forward references
    from tactera_backend import models
    for model_name in dir(models):
        model = getattr(models, model_name)
        if hasattr(model, "update_forward_refs"):
            model.update_forward_refs()

    # Auto-seed (run in sync session safely AFTER DB init)
    AUTO_SEED_ON_START = True
    if AUTO_SEED_ON_START:
        from sqlmodel import Session
        with Session(sync_engine) as session:  # ✅ use sync_engine here
            league_count = len(session.exec(select(League)).all())


            if league_count == 0:
                print("🌱 No leagues found. Auto-seeding database...")
                seed_all()
            else:
                print("✅ Database already seeded. Skipping auto-seed.")

# ✅ Include Routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(club_router, prefix="/clubs", tags=["Clubs"])
app.include_router(player_router, prefix="/players", tags=["Players"])
app.include_router(match_router, prefix="/matches", tags=["Matches"])
app.include_router(league_router, prefix="/leagues", tags=["Leagues"])
app.include_router(training_router, prefix="/training", tags=["Training"])
