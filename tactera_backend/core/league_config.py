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

# league_config.py

league_config = {
    "England": {
        "leagues": [
            {
                "name": "Premier League",   # Tier 1
                "level": 1,
                "teams": 16
            },
            {
                "name": "Division 2",       # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 16},  # Group 1
                    {"teams": 16},  # Group 2
                    {"teams": 16},  # Group 3
                    {"teams": 16}   # Group 4
                ]
            }
        ]
    },
    "Denmark": {
        "leagues": [
            {
                "name": "Superligaen",      # Tier 1
                "level": 1,
                "teams": 14
            },
            {
                "name": "Division 2",       # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 14},  # Group 1
                    {"teams": 14},  # Group 2
                    {"teams": 14},  # Group 3
                    {"teams": 14}   # Group 4
                ]
            }
        ]
    }
}





# ✅ This config will later be imported by seeding scripts and generators.
# Example usage:
# from league_config import league_config
