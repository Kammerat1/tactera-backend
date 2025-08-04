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
