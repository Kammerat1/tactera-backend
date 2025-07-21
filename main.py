from fastapi import FastAPI
from auth import router as auth_router
from club import router as club_router
from match import router as match_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(club_router, prefix="/club")
app.include_router(match_router, prefix="/match")
