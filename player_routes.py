from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import Player
from models import StatLevelRequirement
from typing import Optional
from models import TrainingHistory




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

# 🧪 TEMP ROUTE: Log a training session and apply XP
@router.post("/debug/train-session")
def log_training_session(
    player_id: int = Query(..., description="ID of the player who trained"),
    pace: int = Query(0, description="XP to add to pace"),
    passing: int = Query(0, description="XP to add to passing"),
    defending: int = Query(0, description="XP to add to defending"),
    drill: str = Query(..., description="Name of the drill, e.g., 'Agility Circuit'"),
    note: Optional[str] = Query(None, description="Optional note about the session"),
    session: Session = Depends(get_session),
):
    """
    ⛓️ This route:
    - Adds XP to the player's stats using your existing XP logic
    - Saves a new TrainingSession to the database
    """

    # 🧠 STEP 1: Get the player's current XP and levels BEFORE training
    player = session.get(Player, player_id)
    if not player:
        return {"error": f"Player with ID {player_id} not found."}

    # Store levels before XP is added
    levels_before = {
        "pace": calculate_level_from_xp(player.pace_xp, session),
        "passing": calculate_level_from_xp(player.passing_xp, session),
        "defending": calculate_level_from_xp(player.defending_xp, session),
    }


    # ✅ Add XP to each stat if value is given
    from xp_helper import add_xp_to_stat

    if pace:
        add_xp_to_stat(player_id, "pace", pace, session)
    if passing:
        add_xp_to_stat(player_id, "passing", passing, session)
    if defending:
        add_xp_to_stat(player_id, "defending", defending, session)

            # 🧠 STEP 2: Calculate levels AFTER XP is added
    updated_player = session.get(Player, player_id)

    levels_after = {
        "pace": calculate_level_from_xp(updated_player.pace_xp, session),
        "passing": calculate_level_from_xp(updated_player.passing_xp, session),
        "defending": calculate_level_from_xp(updated_player.defending_xp, session),
    }

    # Compare before/after to detect level-ups
    level_changes = {}
    for stat in ["pace", "passing", "defending"]:
        before = levels_before[stat]
        after = levels_after[stat]
        if before < after:
            level_changes[stat] = f"Level {before} → Level {after} (Leveled up!)"
        else:
            level_changes[stat] = f"Level {before} → Level {after} (No change)"


    # ✅ Save the training session to the database
    new_session = TrainingHistory(
        player_id=player_id,
        pace_xp=pace,
        passing_xp=passing,
        defending_xp=defending,
        drill=drill,
        note=note
    )
    session.add(new_session)
    session.commit()

    return {
        "status": "success",
        "message": "Training session logged and XP applied.",
        "level_changes": level_changes
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
