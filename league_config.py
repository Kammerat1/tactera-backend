"""
league_config.py
----------------
This file defines the configuration for nations, leagues, and divisions in Tactera.
It is used to dynamically generate countries, leagues, divisions, and promotion/relegation rules.

We are starting with:
- England
- Denmark

Later, we can add more nations easily by extending this dictionary.
"""

# 🏆 LEAGUE CONFIGURATION DICTIONARY
"""
league_config.py
----------------
Defines nations, leagues, and divisions for Tactera.
"""

"""
league_config.py
----------------
Defines nations, leagues, and divisions for Tactera.
"""

LEAGUE_CONFIG = {
    "England": {
        "prestige": 85,
        "leagues": [
            {
                "name": "Premier League",  # Tier 1
                "tier": 1,
                "teams": 16,
                "auto_relegations": 3,
                "playoff_relegation": 1,
            },
            {
                "name": "Division 2",  # Tier 2
                "tier": 2,
                "divisions": [
                    {"name": "Division 2 - Group 1", "teams": 12},
                    {"name": "Division 2 - Group 2", "teams": 12},
                    {"name": "Division 2 - Group 3", "teams": 12},
                    {"name": "Division 2 - Group 4", "teams": 12},
                ],
                "auto_promotions": 3,
                "playoff_promotion": 1,
            },
        ],
    },

    "Denmark": {
        "prestige": 70,
        "leagues": [
            {
                "name": "Superligaen",  # Tier 1
                "tier": 1,
                "teams": 14,
                "auto_relegations": 2,
                "survival_playoff": True,
            },
            {
                "name": "Division 2",  # Tier 2
                "tier": 2,
                "divisions": [
                    {"name": "Division 2 - Group 1", "teams": 12},
                    {"name": "Division 2 - Group 2", "teams": 12},
                    {"name": "Division 2 - Group 3", "teams": 12},
                    {"name": "Division 2 - Group 4", "teams": 12},
                ],
                "auto_promotions": 3,
                "playoff_promotion": 1,
            },
        ],
    },
}



# ✅ This config will later be imported by seeding scripts and generators.
# Example usage:
# from league_config import LEAGUE_CONFIG
