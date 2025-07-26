# training.py

import random
from typing import List, Dict

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
        elif roll < 0.75:
            return random.uniform(0.9, 1.1)   # Average
        else:
            return random.uniform(1.1, 1.3)   # Good

    elif consistency >= 70:
        if roll < 0.10:
            return random.uniform(0.6, 0.9)
        elif roll < 0.80:
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
        if roll < 0.4:
            return random.uniform(0.6, 0.9)
        elif roll < 0.9:
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
    ambition_factor = ambition / 100
    potential_factor = potential
    tg_factor = training_ground_boost / 100
    variance = get_consistency_variance(consistency)

    xp = potential_factor * ambition_factor * tg_factor * variance
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
from database import get_session
from models import Club

router = APIRouter()

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

        # Just gather player names + number of stats for now
        training_data.append({
            "player": player.name,
            "num_stats": len(stats)
        })

    return {
        "message": "Loaded players and stats successfully",
        "players": training_data
    }

