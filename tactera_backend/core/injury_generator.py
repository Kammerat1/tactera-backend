import random
from typing import Dict
from tactera_backend.core.injury_config import INJURY_SEVERITY, INJURY_LIST, INJURY_SEVERITY_WEIGHTS

def generate_injury() -> Dict:
    """
    Generate a random injury with severity, duration, and rehab phase details.
    """
    severity = random.choices(
        population=list(INJURY_SEVERITY_WEIGHTS.keys()),
        weights=list(INJURY_SEVERITY_WEIGHTS.values()),
        k=1
    )[0]

    injury = random.choice(INJURY_LIST[severity])
    duration_range = INJURY_SEVERITY[severity]
    days_total = random.randint(duration_range["min_days"], duration_range["max_days"])

    rehab_start = max(1, int(days_total * random.uniform(0.5, 0.7)))
    rehab_xp_multiplier = 0.4 if severity in ["moderate", "severe"] else 0.6
    if severity == "major":
        rehab_xp_multiplier = 0.3

    return {
        "name": injury["name"],
        "type": injury["type"],
        "severity": severity,
        "days_total": days_total,
        "rehab_start": rehab_start,
        "rehab_xp_multiplier": rehab_xp_multiplier,
        "fit_for_matches": False
    }

def calculate_injury_risk(base_risk: float, pitch_quality: int, energy: int, injury_proneness: float) -> float:
    """
    Calculate final injury risk based on:
    - Base risk (e.g., 5%)
    - Pitch quality (lower pitch quality = higher risk)
    - Player energy (fatigue increases risk)
    - Injury proneness (hidden multiplier)
    """
    # Pitch effect: bad pitch increases risk
    pitch_factor = 1 + ((100 - pitch_quality) / 100)

    # Energy effect: tired players are more injury-prone
    energy_factor = 1 + ((100 - energy) / 100)

    # Injury proneness effect: hidden multiplier per player
    proneness_factor = injury_proneness

    # Final combined risk
    return base_risk * pitch_factor * energy_factor * proneness_factor


def calculate_fatigue_modifier(pitch_quality: int) -> float:
    """
    Better pitches reduce energy loss after a match.
    Example:
    - Pitch 90: -20% fatigue impact
    - Pitch 50: normal fatigue
    - Pitch 40: +5% extra fatigue
    """
    return 1 - ((pitch_quality - 50) / 200)
