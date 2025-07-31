from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from tactera_backend.core.database import get_session
from tactera_backend.models.training_model import TrainingHistory, TrainingHistoryStat
from tactera_backend.models.player_model import Player
from tactera_backend.models.stat_level_requirement_model import StatLevelRequirement
from tactera_backend.services.xp_helper import calculate_level_from_xp, add_xp_to_stat
from typing import Optional

router = APIRouter()

# ============================================
# TODO: Refactor this endpoint to use add_xp_to_stat helper.
# Currently manipulates XP directly, bypassing centralized logic.
# ============================================
@router.post("/players/{player_id}/train/{stat_name}")
def train_stat(player_id: int, stat_name: str, xp: int, session: Session = Depends(get_session)):
    """
    Endpoint for training a specific stat by adding XP.
    🚩 TODO: Refactor to use add_xp_to_stat for centralized XP logic.
    """
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    stat_xp_attr = f"{stat_name}_xp"
    if not hasattr(player, stat_xp_attr):
        raise HTTPException(status_code=400, detail=f"Invalid stat name: {stat_name}")

    current_xp = getattr(player, stat_xp_attr)
    new_xp = current_xp + xp
    setattr(player, stat_xp_attr, new_xp)

    new_level = calculate_level_from_xp(new_xp, session)

    session.add(player)
    session.commit()

    return {
        "player_id": player_id,
        "stat_name": stat_name,
        "xp_added": xp,
        "total_xp": new_xp,
        "new_level": new_level,
        "message": f"{stat_name.capitalize()} is now level {new_level}"
    }

# ============================================
# ⚠️ DEBUG ENDPOINT — ADMIN/DEV USE ONLY
# ============================================
@router.get("/debug/levels")
def debug_get_levels(session: Session = Depends(get_session)):
    """
    DEBUG ONLY: Returns all level-to-XP requirements.
    Should be restricted or removed in production.
    """
    statement = select(StatLevelRequirement).order_by(StatLevelRequirement.level)
    results = session.exec(statement).all()
    return [{"level": r.level, "xp_required": r.xp_required} for r in results]

# ============================================
# ⚠️ DEBUG ENDPOINT — ADMIN/DEV USE ONLY
# ============================================
@router.get("/debug/stat-info")
def debug_get_stat_info(
    player_id: int = Query(..., description="ID of the player"),
    stat_name: str = Query(..., description="Name of the stat, like 'pace' or 'passing'"),
    session: Session = Depends(get_session)
):
    """
    DEBUG ONLY: Returns current XP and level for a single stat.
    Example: /debug/stat-info?player_id=1&stat_name=pace
    """
    stat_field_name = f"{stat_name}_xp"
    player = session.get(Player, player_id)
    if not player:
        return {"error": f"Player with ID {player_id} not found."}

    if not hasattr(player, stat_field_name):
        return {"error": f"Stat '{stat_name}' is not valid."}

    xp = getattr(player, stat_field_name)
    level = calculate_level_from_xp(xp, session)
    return {"player_id": player_id, "stat": stat_name, "xp": xp, "level": level}

# ============================================
# Core: Player stat summary
# ============================================
@router.get("/players/{player_id}/stat-summary")
def get_player_stat_summary(player_id: int, session: Session = Depends(get_session)):
    """
    📊 Returns the player's current XP and level for all tracked stats.
    Example: /players/1/stat-summary
    """
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    summary = {
        "pace": {"xp": player.pace_xp, "level": calculate_level_from_xp(player.pace_xp, session)},
        "passing": {"xp": player.passing_xp, "level": calculate_level_from_xp(player.passing_xp, session)},
        "defending": {"xp": player.defending_xp, "level": calculate_level_from_xp(player.defending_xp, session)},
    }
    return {"player_id": player_id, "stats": summary}

# ============================================
# Core: Player stat levels
# ============================================
@router.get("/player/{player_id}/stat-levels")
def get_player_stat_levels(player_id: int, session: Session = Depends(get_session)):
    """
    Returns the player's current XP and calculated level for each stat.
    """
    player = session.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return {
        "player_name": player.name,
        "pace": {"level": calculate_level_from_xp(player.pace_xp, session), "xp": player.pace_xp},
        "passing": {"level": calculate_level_from_xp(player.passing_xp, session), "xp": player.passing_xp},
        "defending": {"level": calculate_level_from_xp(player.defending_xp, session), "xp": player.defending_xp},
    }

# ============================================
# Core: Player training history (paginated)
# ============================================
@router.get("/{player_id}/training/history")
def get_player_training_history(
    player_id: int,
    session: Session = Depends(get_session),
    page: int = 1,
    limit: int = 100
):
    """
    Returns a player's training history with drill names, XP gained, and stat updates.
    Paginated: ?page=1&limit=100
    """
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found.")

    total_count = len(
        session.exec(select(TrainingHistoryStat).where(TrainingHistoryStat.player_id == player_id)).all()
    )
    offset = (page - 1) * limit

    stat_entries = session.exec(
        select(TrainingHistoryStat)
        .where(TrainingHistoryStat.player_id == player_id)
        .order_by(TrainingHistoryStat.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    history = []
    for stat_entry in stat_entries:
        history_record = session.get(TrainingHistory, stat_entry.history_id)
        history.append({
            "date": history_record.date,
            "drill_name": history_record.drill_name,
            "stat_name": stat_entry.stat_name,
            "xp_gained": stat_entry.xp_gained,
            "new_value": stat_entry.new_value
        })

    return {
        "player_id": player_id,
        "player_name": player.name,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "history": history
    }
