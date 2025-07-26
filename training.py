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

