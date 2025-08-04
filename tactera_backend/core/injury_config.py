# tactera_backend/core/injury_config.py

from typing import Dict, List

# 🔥 Severity tiers control recovery time and impact severity
INJURY_SEVERITY = {

    "minor": {"min_days": 1, "max_days": 2},     # Light injuries (can train lightly)
    "moderate": {"min_days": 3, "max_days": 5},  # Miss a few matches
    "severe": {"min_days": 6, "max_days": 10},   # Out most of a season
    "major": {"min_days": 11, "max_days": 20},   # Rare, season-ending injuries
}

# ⚽ List of injuries grouped by severity
INJURY_LIST: Dict[str, List[Dict]] = {
    "minor": [
        {"name": "Bruised Thigh", "type": "muscle"},
        {"name": "Light Ankle Sprain", "type": "joint"},
        {"name": "Groin Pull", "type": "muscle"},
        {"name": "Bruised Ribs", "type": "impact"},
    ],
    "moderate": [
        {"name": "Hamstring Strain", "type": "muscle"},
        {"name": "Calf Strain", "type": "muscle"},
        {"name": "Twisted Knee", "type": "joint"},
        {"name": "Concussion", "type": "impact"},
    ],
    "severe": [
        {"name": "Fractured Arm", "type": "bone"},
        {"name": "Dislocated Shoulder", "type": "joint"},
        {"name": "Torn Quadriceps", "type": "muscle"},
        {"name": "Torn Ligament", "type": "joint"},
    ],
    "major": [
        {"name": "ACL Tear", "type": "joint"},
        {"name": "Compound Fracture", "type": "bone"},
        {"name": "Achilles Tendon Rupture", "type": "muscle"},
    ],
}

# ⚖️ Weighted chance of severity occurring when injury happens
INJURY_SEVERITY_WEIGHTS = {
    "minor": 0.65,      # 65% chance of minor injuries
    "moderate": 0.25,   # 25% moderate
    "severe": 0.08,     # 8% severe
    "major": 0.02,      # 2% major (rare)
}
