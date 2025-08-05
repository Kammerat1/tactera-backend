from sqlalchemy.ext.asyncio import AsyncSession
from tactera_backend.services.injury_service import tick_injuries

async def process_daily_tick(db: AsyncSession):
    """
    Advances the game by one day:
    - Decrements injury timers
    (Future: training XP, match scheduling, contracts, etc.)
    """
    injury_result = await tick_injuries(db)

    return {
        "message": "Daily tick processed.",
        "injuries_updated": injury_result["updated_injuries"],
        "injury_details": injury_result["injuries"]
    }
