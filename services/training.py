# training.py

import random
from typing import List, Dict
from tactera_backend.models.club import Club # Club model
from tactera_backend.models.training_models import TrainingGround  # Core model
from tactera_backend.models.player_stat import PlayerStat  # Stat model lives in separate file
from tactera_backend.models.player import Player  # Player model lives in separate file


# === DRILL DEFINITIONS ===
# Each drill contains a name and a list of affected stats
DRILLS = [
    {
        "name": "Quick Passing",
        "affected_stats": ["passing", "vision", "first_touch"]
    },
    {
        "name": "Finishing Touch",
        "affected_stats": ["finishing", "positioning"]
    },
    {
        "name": "Endurance Run",
        "affected_stats": ["stamina", "pace", "strength"]
    },
    {
        "name": "Defensive Shape",
        "affected_stats": ["tackling", "positioning", "stamina"]
    },
    {
        "name": "Technique Circuit",
        "affected_stats": ["dribbling", "first_touch", "vision"]
    },
    {
        "name": "Squad Cohesion",
        "affected_stats": ["passing", "vision", "stamina", "strength", "positioning"]
    },
    {
        "name": "1v1 Challenge",
        "affected_stats": ["pace", "tackling", "dribbling", "finishing"]
    },
     {
        "name": "Friendly Match",
        "affected_stats": ["passing", "finishing", "dribbling", "tackling", "first_touch",
            "vision", "positioning", "pace", "stamina", "strength"]
    },
]

def get_drill_by_name(name: str) -> Dict:
    """Fetch a drill definition by its name (case-insensitive)"""
    for drill in DRILLS:
        if drill["name"].lower() == name.lower():
            return drill
    raise ValueError(f"Drill '{name}' not found.")


# === XP CALCULATION ===

def get_consistency_variance(consistency: int) -> float:
    """Return a multiplier based on consistency using a probabilistic model"""
    roll = random.uniform(0, 1)

    if consistency >= 90:
        if roll < 0.05:
            return random.uniform(0.6, 0.9)   # Bad
        elif roll < 0.50:
            return random.uniform(0.9, 1.1)   # Average
        else:
            return random.uniform(1.1, 1.3)   # Good

    elif consistency >= 70:
        if roll < 0.10:
            return random.uniform(0.6, 0.9)
        elif roll < 0.70:
            return random.uniform(0.9, 1.1)
        else:
            return random.uniform(1.1, 1.3)

    elif consistency >= 50:
        if roll < 0.15:
            return random.uniform(0.6, 0.9)
        elif roll < 0.85:
            return random.uniform(0.9, 1.1)
        else:
            return random.uniform(1.1, 1.3)

    elif consistency >= 30:
        if roll < 0.25:
            return random.uniform(0.6, 0.9)
        elif roll < 0.90:
            return random.uniform(0.9, 1.1)
        else:
            return random.uniform(1.1, 1.3)

    else:
        if roll < 0.40:
            return random.uniform(0.6, 0.9)
        elif roll < 0.90:
            return random.uniform(0.9, 1.1)
        else:
            return random.uniform(1.1, 1.3)


def calculate_training_xp(
    potential: int,
    ambition: int,
    consistency: int,
    training_ground_boost: int
) -> float:
    

    """
    Calculate the total XP a player earns in a training session.

    XP = potential × ambition modifier × training ground boost × consistency variance
    """
    potential_factor = potential
    if ambition >= 95:
        ambition_factor = 1.2
    elif ambition >= 90:
        ambition_factor = 1.1
    elif ambition >= 80:
        ambition_factor = 1.0
    elif ambition >= 60:
        ambition_factor = 0.9
    elif ambition >= 40:
        ambition_factor = 0.70
    else:
        ambition_factor = 0.6
    tg_factor = (training_ground_boost / 100)
    variance = get_consistency_variance(consistency)

    xp = (potential ** 1.15) * ambition_factor * tg_factor * variance
    return round(xp, 2)

def split_xp_among_stats(total_xp: float, stat_list: List[str]) -> Dict[str, float]:
    """
    Splits total XP among stats with +/- 20% random variation.
    Returns a dict: {stat_name: xp}
    """
    base_xp = total_xp / len(stat_list)
    stat_xp = {}

    for stat in stat_list:
        variation = random.uniform(0.8, 1.2)  # +/-20%
        xp = round(base_xp * variation, 2)
        stat_xp[stat] = xp

    return stat_xp


# training.py (continued)

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from datetime import date
from tactera_backend.core.database import get_session
from tactera_backend.models.models import Club

router = APIRouter()

'''
# DEPRECATED - NOW IN CLUB.PY
@router.post("/clubs/{club_id}/train")
def train_club(club_id: int, session: Session = Depends(get_session)):
    # Get today's date
    today = date.today()

    # Load the club
    club = session.exec(select(Club).where(Club.id == club_id)).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Check if already trained today
    if club.last_training_date == today:
        raise HTTPException(status_code=403, detail="Club has already trained today")

    # Load all players in the club
    players = session.exec(select(Player).where(Player.club_id == club.id)).all()

    if not players:
        raise HTTPException(status_code=404, detail="No players found in this club")

    # Load stats for each player
    training_data = []

    for player in players:
        stats = session.exec(select(PlayerStat).where(PlayerStat.player_id == player.id)).all()

        drill = get_drill_by_name("1v1 Challenge")

        tg = session.exec(
            select(TrainingGround).where(TrainingGround.id == club.trainingground_id)
        ).first()
        tg_boost = tg.xp_boost if tg else 100

        total_xp = calculate_training_xp(
            potential=player.potential,
            ambition=player.ambition,
            consistency=player.consistency,
            training_ground_boost=tg_boost
        )

        xp_split = split_xp_among_stats(total_xp, drill["affected_stats"])

        updated_stats = []

        for stat in stats:
            if stat.stat_name in xp_split:
                stat.xp += xp_split[stat.stat_name]
                updated_stats.append({"stat": stat.stat_name, "xp_gained": xp_split[stat.stat_name]})

        training_data.append({
            "player": player.name,
            "total_xp": total_xp,
            "updated_stats": updated_stats
        })

    # Set the cooldown
    club.last_training_date = today

    # Save all updates
    session.add(club)
    session.commit()


    return {
        "message": "Training complete (dry run)",
        "players": training_data
    } '''


