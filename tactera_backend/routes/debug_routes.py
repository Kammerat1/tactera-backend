from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from tactera_backend.core.database import get_db
from tactera_backend.models.player_model import Player

router = APIRouter()

@router.get("/debug/players")
async def debug_list_players(db: AsyncSession = Depends(get_db)):
    """
    Debug endpoint: List all players with their first/last name and club ID.
    """
    result = await db.execute(select(Player))
    players = result.scalars().all()
    return [
        {
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "club_id": p.club_id
        }
        for p in players
    ]

from typing import Literal, Optional
from fastapi import Body, HTTPException
from sqlmodel import select
from tactera_backend.models.club_model import Club
from tactera_backend.core.training_intensity import ALLOWED_INTENSITIES

@router.get("/debug/club/{club_id}/training-intensity")
async def get_club_training_intensity(club_id: int, db: AsyncSession = Depends(get_db)):
    """Return the club's current training intensity setting."""
    club = await db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return {"club_id": club_id, "training_intensity": club.training_intensity}

@router.post("/debug/club/{club_id}/training-intensity")
async def set_club_training_intensity(
    club_id: int,
    intensity: Literal["light", "normal", "hard"] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """
    Set the club's training intensity.
    Hybrid rule (future): 'hard' requires physio dept >= 1.
    For now, we allow all three and will enforce when physio exists.
    """
    club = await db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    intensity = intensity.lower()
    if intensity not in ALLOWED_INTENSITIES:
        raise HTTPException(status_code=400, detail=f"Invalid intensity. Allowed: {sorted(ALLOWED_INTENSITIES)}")

    # TODO (future): enforce 'hard' lock behind physio department >= 1
    club.training_intensity = intensity
    db.add(club)
    await db.commit()
    await db.refresh(club)

    return {
        "club_id": club_id,
        "training_intensity": club.training_intensity,
        "note": "Hard will be locked behind physio later.",
    }
