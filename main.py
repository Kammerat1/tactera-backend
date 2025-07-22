from fastapi import FastAPI
from sqlmodel import SQLModel
from models import Manager, Club, Player, MatchResult, TrainingGround
from sqlmodel import Session


from auth import router as auth_router
from club import router as club_router
from match import router as match_router
from player_routes import router as player_router
from seed_xp_levels import safe_seed_stat_levels



from database import init_db, engine  # ✅ Add engine import here


app = FastAPI()
init_db()

# ✅ Automatically seed the XP levels if table is empty
safe_seed_stat_levels()

app.include_router(auth_router, prefix="/auth")
app.include_router(club_router, prefix="/club")
app.include_router(match_router, prefix="/match")
app.include_router(player_router)
