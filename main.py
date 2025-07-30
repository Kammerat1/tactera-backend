from sqlmodel import SQLModel, Session
from fastapi import FastAPI
from tactera_backend.models.player_stat import PlayerStat
from tactera_backend.models.models import Club, MatchResult, TrainingGround
from tactera_backend.models.manager import Manager
from tactera_backend.models.player import Player
from tactera_backend.models.models import*  # This ensures Stadium + StadiumPart are included



from tactera_backend.core.auth import router as auth_router
from tactera_backend.models.club import router as club_router
from tactera_backend.services.match import router as match_router
from tactera_backend.routes.player_routes import router as player_router
from tactera_backend.seed.seed_xp_levels import safe_seed_stat_levels
from tactera_backend.routes.league_routes import router as league_router




from tactera_backend.core.database import init_db, engine  # ✅ Add engine import here





app = FastAPI()
init_db()

# ✅ Create all tables including Stadium and StadiumPart
SQLModel.metadata.create_all(engine)


# ✅ Automatically seed the XP levels if table is empty
safe_seed_stat_levels()

app.include_router(auth_router, prefix="/auth")
app.include_router(club_router, prefix="/club")
app.include_router(match_router, prefix="/match")
app.include_router(player_router)
app.include_router(league_router)

# 🧩 Import the training route
from tactera_backend.services.training import router as training_router

# 🔌 Connect the training route to the FastAPI app
# This will activate /clubs/{club_id}/train in Swagger and in the API
app.include_router(training_router)
