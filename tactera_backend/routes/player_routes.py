from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from tactera_backend.core.database import get_session, get_db
from tactera_backend.models.training_model import TrainingHistory, TrainingHistoryStat
from tactera_backend.models.player_model import Player
from tactera_backend.models.stat_level_requirement_model import StatLevelRequirement
from tactera_backend.services.xp_helper import calculate_level_from_xp, add_xp_to_stat
from typing import Optional
from tactera_backend.services.injury_service import tick_injuries
from sqlalchemy.ext.asyncio import AsyncSession

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
        f"{player.first_name} {player.last_name}"
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
        "name": f"{player.first_name} {player.last_name}",
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "history": history
    }
    
    # ================================
    # DEBUG: TICK INJURIES
    # ================================

@router.post("/debug/tick-injuries")
async def debug_tick_injuries(db: AsyncSession = Depends(get_db)):
    """
    Debug: Progress injury recovery by 1 day for all injured players.
    """
    result = await tick_injuries(db)
    return result

# ================================
# LIST CURRENT INJURIES
# ================================
from tactera_backend.models.injury_model import Injury
from sqlmodel import select

@router.get("/injuries")
async def list_current_injuries(db: AsyncSession = Depends(get_db)):
    """
    Lists all currently injured players and their injury details.
    """
    result = await db.execute(select(Injury).where(Injury.days_remaining > 0))
    injuries = result.scalars().all()

    return [
        {
            "player_id": i.player_id,
            "injury": i.name,
            "severity": i.severity,
            "days_remaining": i.days_remaining,
            "fit_for_matches": i.fit_for_matches
        }
        for i in injuries
    ]

from tactera_backend.services.game_tick_service import process_daily_tick

@router.post("/debug/daily-tick")
async def debug_daily_tick(db: AsyncSession = Depends(get_db)):
    """
    Debug: Advances the game by 1 in-game day and processes all daily updates.
    """
    return await process_daily_tick(db)

from tactera_backend.models.player_model import Player, PlayerRead
from tactera_backend.models.injury_model import Injury
import pytz

# ✅ UTC+2 timezone (Europe/Copenhagen) for injury date consistency
utc_plus_2 = pytz.timezone("Europe/Copenhagen")

@router.get("/players/{player_id}", response_model=PlayerRead)
def get_player(player_id: int, session: Session = Depends(get_session)):
    """
    Fetch a single player by ID and include their active injury if present.
    - Returns injury details (name, severity, days remaining, rehab info).
    - Injury dates are returned in UTC+2.
    """
    # 🔎 Retrieve player by ID
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # ✅ Find active injury (if any: days_remaining > 0)
    active_injury = None
    if player.injuries:
        for injury in player.injuries:
            if injury.days_remaining > 0:
                injury.start_date = injury.start_date.astimezone(utc_plus_2)
                active_injury = injury
                print(f"[DEBUG] Active injury for {player.first_name} {player.last_name}: {injury.name}")
                break
        if not active_injury:
            print(f"[DEBUG] No active injuries for {player.first_name} {player.last_name}")
    else:
        print(f"[DEBUG] Player {player.first_name} {player.last_name} has no injury history.")

    # ✅ Return player with injury info attached
    return PlayerRead.from_orm(player).copy(update={"active_injury": active_injury})


from datetime import timedelta
import pytz

utc_plus_2 = pytz.timezone("Europe/Copenhagen")

@router.get("/players/{player_id}/injuries")
def get_player_injury_history(player_id: int, session: Session = Depends(get_session)):
    """
    Returns the full injury history for a player (active + healed).
    Includes end_date for healed injuries. Dates are UTC+2.
    """
    # 1️⃣ Fetch player
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # 2️⃣ Query all injuries
    injuries = session.exec(select(Injury).where(Injury.player_id == player_id)).all()

    if not injuries:
        return {
            "player_id": player_id,
            "player_name": f"{player.first_name} {player.last_name}",
            "injuries": []
        }

    # 3️⃣ Build response
    history = []
    for injury in injuries:
        start_utc2 = injury.start_date.astimezone(utc_plus_2)
        end_date = None
        if injury.days_remaining == 0:
            end_date = (injury.start_date + timedelta(days=injury.days_total)).astimezone(utc_plus_2)

        history.append({
            "name": injury.name,
            "type": injury.type,
            "severity": injury.severity,
            "start_date": start_utc2,
            "end_date": end_date,  # ✅ New field
            "days_total": injury.days_total,
            "days_remaining": injury.days_remaining,
            "rehab_start": injury.rehab_start,
            "rehab_xp_multiplier": injury.rehab_xp_multiplier,
            "fit_for_matches": injury.fit_for_matches,
            "active": injury.days_remaining > 0
        })

    return {
        "player_id": player_id,
        "player_name": f"{player.first_name} {player.last_name}",
        "injuries": history
    }
