from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import Player
from xp_helper import calculate_level_from_xp
from models import StatLevelRequirement


router = APIRouter()

@router.post("/players/{player_id}/train/{stat_name}")
def train_stat(player_id: int, stat_name: str, xp: int, session: Session = Depends(get_session)):
    """
    Endpoint for training a specific stat by adding XP.

    - player_id: ID of the player to train
    - stat_name: Name of the stat to train (e.g., "pace", "passing", "defending")
    - xp: Amount of XP to add to that stat
    """

    # 1. Get the player from the database
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # 2. Get the stat's current XP field name and level
    stat_xp_attr = f"{stat_name}_xp"

    if not hasattr(player, stat_xp_attr):
        raise HTTPException(status_code=400, detail=f"Invalid stat name: {stat_name}")

    # 3. Get current XP
    current_xp = getattr(player, stat_xp_attr)

    # 4. Add new XP
    new_xp = current_xp + xp
    setattr(player, stat_xp_attr, new_xp)

    # 5. Calculate level from total XP
    new_level = calculate_level_from_xp(new_xp, session)

    # 6. Commit changes
    session.add(player)
    session.commit()

    # 7. Return a response
    return {
        "player_id": player_id,
        "stat_name": stat_name,
        "xp_added": xp,
        "total_xp": new_xp,
        "new_level": new_level,
        "message": f"{stat_name.capitalize()} is now level {new_level}"
    }

# Debug route to check the level XP table
@router.get("/debug/levels")
def debug_get_levels(session: Session = Depends(get_session)):
    statement = select(StatLevelRequirement).order_by(StatLevelRequirement.level)
    results = session.exec(statement).all()
    return [{"level": r.level, "xp_required": r.xp_required} for r in results]
