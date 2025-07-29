from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import Player
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
from xp_helper import calculate_level_from_xp
from xp_helper import add_xp_to_stat  # Import the helper we just made

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

@router.get("/players/{player_id}/stat-summary")
def get_player_stat_summary(player_id: int, session: Session = Depends(get_session)):
    """
    📊 Returns the player's current XP and level for all three stats.
    Example: /players/1/stat-summary
    """

    # 🧠 STEP 1: Get the player from the database
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # 🧠 STEP 2: Calculate level for each stat using their XP
    summary = {
        "pace": {
            "xp": player.pace_xp,
            "level": calculate_level_from_xp(player.pace_xp, session)
        },
        "passing": {
            "xp": player.passing_xp,
            "level": calculate_level_from_xp(player.passing_xp, session)
        },
        "defending": {
            "xp": player.defending_xp,
            "level": calculate_level_from_xp(player.defending_xp, session)
        },
    }

    # ✅ Return structured stat summary
    return {
        "player_id": player_id,
        "stats": summary
    }

# 🧠 ROUTE: View a player's current stat levels and XP
@router.get("/player/{player_id}/stat-levels")
def get_player_stat_levels(player_id: int, session: Session = Depends(get_session)):
    """
    Returns the player's current XP and calculated level for each stat.
    """
    # Look up the player by ID
    player = session.query(Player).filter(Player.id == player_id).first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Calculate levels using XP values
    pace_level = calculate_level_from_xp(player.pace_xp, session)
    passing_level = calculate_level_from_xp(player.passing_xp, session)
    defending_level = calculate_level_from_xp(player.defending_xp, session)

    return {
        "player_name": player.name,
        "pace": {
            "level": pace_level,
            "xp": player.pace_xp
        },
        "passing": {
            "level": passing_level,
            "xp": player.passing_xp
        },
        "defending": {
            "level": defending_level,
            "xp": player.defending_xp
        }
    }
