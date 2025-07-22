from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import Player
from xp_helper import calculate_level_from_xp
from models import StatLevelRequirement
from typing import Optional



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


# ⚠️ TEMPORARY DEBUG ROUTE — used to simulate training by adding XP to a player's stat

from fastapi import Query  # Add this at the top if not already imported
from xp_helper import add_xp_to_stat  # Import the helper we just made

@router.get("/debug/train")
def debug_add_xp_to_stat(
    player_id: int = Query(..., description="ID of the player"),
    stat_name: str = Query(..., description="Name of the stat, like 'pace' or 'passing'"),
    xp_amount: int = Query(..., description="Amount of XP to add"),
    session: Session = Depends(get_session)
):
    """
    Temporary route to simulate training by adding XP to a player's stat.

    Example: /debug/train?player_id=1&stat_name=pace&xp_amount=40
    """

    try:
        # Try to add the XP using our helper function
        add_xp_to_stat(player_id, stat_name, xp_amount, session)

        return {"message": f"Added {xp_amount} XP to {stat_name} for player {player_id}."}

    except ValueError as e:
        # If something went wrong (like invalid stat or player), return the error message
        return {"error": str(e)}
    
    # ⚠️ TEMPORARY DEBUG ROUTE — shows XP and level for one stat on a player

from xp_helper import calculate_level_from_xp  # Already in use earlier

@router.get("/debug/stat-info")
def debug_get_stat_info(
    player_id: int = Query(..., description="ID of the player"),
    stat_name: str = Query(..., description="Name of the stat, like 'pace' or 'passing'"),
    session: Session = Depends(get_session)
):
    """
    Returns current XP and level for a single stat on a given player.
    Example: /debug/stat-info?player_id=1&stat_name=pace
    """

    # Build the database field name (e.g., pace_xp)
    stat_field_name = f"{stat_name}_xp"

    # Get the player from the database
    player = session.get(Player, player_id)
    if not player:
        return {"error": f"Player with ID {player_id} not found."}

    # Make sure the stat exists
    if not hasattr(player, stat_field_name):
        return {"error": f"Stat '{stat_name}' is not valid."}

    # Get XP for this stat
    xp = getattr(player, stat_field_name)

    # Calculate level based on XP
    level = calculate_level_from_xp(xp, session)

    return {
        "player_id": player_id,
        "stat": stat_name,
        "xp": xp,
        "level": level
    }

# ⚠️ TEMPORARY DEBUG ROUTE — simulates a full training session by adding XP to multiple stats

@router.get("/debug/train-session")
def debug_train_session(
    player_id: int = Query(..., description="ID of the player"),
    pace: Optional[int] = Query(0, description="XP to add to pace"),
    passing: Optional[int] = Query(0, description="XP to add to passing"),
    defending: Optional[int] = Query(0, description="XP to add to defending"),
    session: Session = Depends(get_session)
):
    """
    Adds XP to multiple stats in one go, simulating a full training session.
    Example: /debug/train-session?player_id=1&pace=40&passing=20
    """

    response = {}
    try:
        if pace > 0:
            add_xp_to_stat(player_id, "pace", pace, session)
            response["pace"] = f"+{pace} XP"

        if passing > 0:
            add_xp_to_stat(player_id, "passing", passing, session)
            response["passing"] = f"+{passing} XP"

        if defending > 0:
            add_xp_to_stat(player_id, "defending", defending, session)
            response["defending"] = f"+{defending} XP"

        if not response:
            return {"message": "No stats were updated."}

        return {
            "player_id": player_id,
            "updated_stats": response
        }

    except ValueError as e:
        return {"error": str(e)}
