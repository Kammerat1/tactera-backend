from fastapi import FastAPI
from sqlmodel import select, Session
from tactera_backend.core.database import init_db, sync_engine
from tactera_backend.seed.seed_all import seed_all
from tactera_backend.models.league_model import League

# --- Routers ---
from tactera_backend.core.auth import router as auth_router
from tactera_backend.routes.club_routes import router as club_router
from tactera_backend.services.match import router as match_router
from tactera_backend.routes.player_routes import router as player_router
from tactera_backend.routes.league_routes import router as league_router
from tactera_backend.services.training import router as training_router
from tactera_backend.routes.stadium_routes import router as stadium_router
from tactera_backend.routes.debug_routes import router as debug_router

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    # 1️⃣ Init DB tables async
    await init_db()

    # 2️⃣ Resolve forward references
    from tactera_backend import models
    for model_name in dir(models):
        model = getattr(models, model_name)
        if hasattr(model, "update_forward_refs"):
            model.update_forward_refs()

    # 3️⃣ Auto-seed DB in sync mode
    with Session(sync_engine) as session:
        league_count = len(session.exec(select(League)).all())
        if league_count == 0:
            print("🌱 No leagues found. Auto-seeding database...")
            seed_all()  # ✅ Uses sync engine only
        else:
            print("✅ Database already seeded. Skipping auto-seed.")

# Routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(club_router, prefix="/clubs", tags=["Clubs"])
app.include_router(player_router, prefix="/players", tags=["Players"])
app.include_router(match_router, prefix="/matches", tags=["Matches"])
app.include_router(league_router, prefix="/leagues", tags=["Leagues"])
app.include_router(training_router, prefix="/training", tags=["Training"])
app.include_router(stadium_router, prefix="/stadiums", tags=["Stadiums"])
app.include_router(debug_router, tags=["Debug"])
