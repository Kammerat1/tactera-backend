# training.py

import random
from typing import List, Dict
from tactera_backend.models.club_model import Club # Club model
from tactera_backend.models.training_model import TrainingGround  # Core model
from tactera_backend.models.player_stat_model import PlayerStat  # Stat model lives in separate file
from tactera_backend.models.player_model import Player  # Player model lives in separate file
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from datetime import date
from tactera_backend.core.database import get_session
from tactera_backend.models.club_model import Club
from tactera_backend.core.training_intensity import get_xp_multiplier, calculate_energy_drain



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
    tg_factor = (1 + training_ground_boost / 100)
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

router = APIRouter()


# --- INJURY-AWARE TRAINING HELPER ---

from tactera_backend.models.injury_model import Injury  # ✅ Needed to check injuries

def apply_training_with_injury_check(player: Player, drill: Dict, session: Session) -> Dict:
    """
    Applies training XP to a player, respecting injury and rehab status.
    - Fully injured players: skipped.
    - Rehab-phase players: forced to light training XP.
    - Healthy players: normal training.
    Returns a structured result dict.
    """
    # ✅ 1. Check if player has an active injury
    active_injury = session.exec(
        select(Injury).where(Injury.player_id == player.id).order_by(Injury.start_date.desc())
    ).first()

    if active_injury:
    # Phase 1: Fully out (cannot train at all)
        if active_injury.days_remaining > active_injury.rehab_start:
            return {
                "player": f"{player.first_name} {player.last_name}",
                "status_flag": "skipped",
                "xp_applied": 0,
                "updated_stats": [],
                "notes": f"Injury: {active_injury.name} (fully out)"
            }


        # Phase 2: Rehab (auto-light training)
        training_intensity = "light"
        rehab_penalty = 0.5  # ✅ Only 50% XP efficiency during rehab
    else:
        # No injury: normal training
        training_intensity = "normal"
        rehab_penalty = 1.0

    # ✅ 2. Calculate XP
    tg = session.exec(
        select(TrainingGround).where(TrainingGround.id == player.club.trainingground_id)
    ).first()
    tg_boost = tg.xp_boost if tg else 100

    total_xp = calculate_training_xp(
        potential=player.potential,
        ambition=player.ambition,
        consistency=player.consistency,
        training_ground_boost=tg_boost
    )

    # ✅ 3. Apply rehab penalty if needed
    total_xp *= rehab_penalty

    # --- INTENSITY APPLICATION (XP + ENERGY) ---
    # Determine the club's chosen intensity, defaulting to "normal"
    club_intensity = (player.club.training_intensity if player and player.club else "normal").lower()

    # If the player is in rehab (allowed training), force light intensity for safety.
    effective_intensity = club_intensity
    if active_injury:
        # If the player is in the rehab phase, we force light.
        if active_injury.days_remaining <= active_injury.rehab_start:
            effective_intensity = "light"

    # Apply XP multiplier to the already computed base_xp
    xp_mult = get_xp_multiplier(effective_intensity)
    base_xp = base_xp * xp_mult  # base_xp exists earlier in this function

    # Apply energy drain and persist
    energy_before = player.energy
    energy_drain = calculate_energy_drain(effective_intensity)
    player.energy = max(0, player.energy - energy_drain)
    session.add(player)  # make sure energy change is saved later

    # ✅ 4. Split XP across stats
    xp_split = split_xp_among_stats(total_xp, drill["affected_stats"])

    # ✅ 5. Update player stats
    updated_stats = []
    for stat in session.exec(select(PlayerStat).where(PlayerStat.player_id == player.id)).all():
        if stat.stat_name in xp_split:
            stat.xp += xp_split[stat.stat_name]
            updated_stats.append({"stat": stat.stat_name, "xp_gained": xp_split[stat.stat_name]})
    session.commit()

    return {
        "player": f"{player.first_name} {player.last_name}",
        "status_flag": "rehab-light" if active_injury and active_injury.days_remaining <= active_injury.rehab_start 
                       else "skipped" if active_injury and active_injury.days_remaining > active_injury.rehab_start 
                       else "normal",
        "xp_applied": round(total_xp, 2),
        "training_intensity_used": effective_intensity,
        "energy_before": energy_before,
        "energy_after": player.energy,
        "energy_drain": energy_drain,

        "updated_stats": updated_stats,
        "notes": f"Injury: {active_injury.name} (rehab phase)" if active_injury and active_injury.days_remaining <= active_injury.rehab_start 
                 else f"Injury: {active_injury.name} (fully out)" if active_injury 
                 else "Healthy"
    }

