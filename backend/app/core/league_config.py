# tactera_backend/core/league_config.py
"""
league_config.py
----------------
Defines nations, leagues, and divisions for Tactera.

✅ 10-COUNTRY EXPANSION COMPLETE
- 2 Active countries for beta launch: England, Denmark  
- 8 Inactive countries ready for future activation
- Two-system design: Compact (14 teams) vs Extended (18 teams)
- Dynamic reputation system prepared
"""

league_config = {
    # ==========================================
    # 🇬🇧 ENGLAND - EXTENDED SYSTEM (ACTIVE)
    # ==========================================
    "England": {
        "active": True,          # ✅ BETA ACTIVE
        "system": "extended",    # 18 teams, 34 rounds, 16.7% relegation
        "reputation": 92,        # Premier League - elite level (scale 1-100)
        "leagues": [
            {
                "name": "Premier League",   # Tier 1
                "level": 1,
                "teams": 18
            },
            {
                "name": "Division 2",       # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 18},  # Group 1
                    {"teams": 18},  # Group 2
                    {"teams": 18},  # Group 3
                    {"teams": 18}   # Group 4
                ]
            }
        ]
    },

    # ==========================================
    # 🇩🇰 DENMARK - COMPACT SYSTEM (ACTIVE) 
    # ==========================================
    "Denmark": {
        "active": True,          # ✅ BETA ACTIVE
        "system": "compact",     # 14 teams, 26 rounds, 21.4% relegation
        "reputation": 75,        # Superligaen - good level, smaller nation
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
    },

    # ==========================================
    # 🇩🇪 GERMANY - EXTENDED SYSTEM (INACTIVE)
    # ==========================================
    "Germany": {
        "active": False,         # 🚧 PREPARED FOR FUTURE
        "system": "extended",    # 18 teams, 34 rounds, 16.7% relegation
        "reputation": 95,        # Bundesliga - highest reputation
        "leagues": [
            {
                "name": "Bundesliga",       # Tier 1
                "level": 1,
                "teams": 18
            },
            {
                "name": "2. Bundesliga",    # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 18},  # Group 1
                    {"teams": 18},  # Group 2
                    {"teams": 18},  # Group 3
                    {"teams": 18}   # Group 4
                ]
            }
        ]
    },

    # ==========================================
    # 🇪🇸 SPAIN - EXTENDED SYSTEM (INACTIVE)
    # ==========================================
    "Spain": {
        "active": False,         # 🚧 PREPARED FOR FUTURE
        "system": "extended",    # 18 teams, 34 rounds, 16.7% relegation
        "reputation": 94,        # La Liga - elite level
        "leagues": [
            {
                "name": "La Liga",          # Tier 1
                "level": 1,
                "teams": 18
            },
            {
                "name": "Segunda División", # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 18},  # Group 1
                    {"teams": 18},  # Group 2
                    {"teams": 18},  # Group 3
                    {"teams": 18}   # Group 4
                ]
            }
        ]
    },

    # ==========================================
    # 🇮🇹 ITALY - EXTENDED SYSTEM (INACTIVE)
    # ==========================================
    "Italy": {
        "active": False,         # 🚧 PREPARED FOR FUTURE
        "system": "extended",    # 18 teams, 34 rounds, 16.7% relegation
        "reputation": 90,        # Serie A - strong reputation
        "leagues": [
            {
                "name": "Serie A",          # Tier 1
                "level": 1,
                "teams": 18
            },
            {
                "name": "Serie B",          # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 18},  # Group 1
                    {"teams": 18},  # Group 2
                    {"teams": 18},  # Group 3
                    {"teams": 18}   # Group 4
                ]
            }
        ]
    },

    # ==========================================
    # 🇫🇷 FRANCE - EXTENDED SYSTEM (INACTIVE)
    # ==========================================
    "France": {
        "active": False,         # 🚧 PREPARED FOR FUTURE
        "system": "extended",    # 18 teams, 34 rounds, 16.7% relegation
        "reputation": 88,        # Ligue 1 - strong reputation
        "leagues": [
            {
                "name": "Ligue 1",          # Tier 1
                "level": 1,
                "teams": 18
            },
            {
                "name": "Ligue 2",          # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 18},  # Group 1
                    {"teams": 18},  # Group 2
                    {"teams": 18},  # Group 3
                    {"teams": 18}   # Group 4
                ]
            }
        ]
    },

    # ==========================================
    # 🇳🇱 NETHERLANDS - EXTENDED SYSTEM (INACTIVE)
    # ==========================================
    "Netherlands": {
        "active": False,         # 🚧 PREPARED FOR FUTURE
        "system": "extended",    # 18 teams, 34 rounds, 16.7% relegation
        "reputation": 82,        # Eredivisie - good reputation
        "leagues": [
            {
                "name": "Eredivisie",       # Tier 1
                "level": 1,
                "teams": 18
            },
            {
                "name": "Eerste Divisie",   # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 18},  # Group 1
                    {"teams": 18},  # Group 2
                    {"teams": 18},  # Group 3
                    {"teams": 18}   # Group 4
                ]
            }
        ]
    },

    # ==========================================
    # 🇵🇹 PORTUGAL - COMPACT SYSTEM (INACTIVE)
    # ==========================================
    "Portugal": {
        "active": False,         # 🚧 PREPARED FOR FUTURE
        "system": "compact",     # 14 teams, 26 rounds, 21.4% relegation
        "reputation": 78,        # Primeira Liga - decent reputation
        "leagues": [
            {
                "name": "Primeira Liga",    # Tier 1
                "level": 1,
                "teams": 14
            },
            {
                "name": "Liga 2",           # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 14},  # Group 1
                    {"teams": 14},  # Group 2
                    {"teams": 14},  # Group 3
                    {"teams": 14}   # Group 4
                ]
            }
        ]
    },

    # ==========================================
    # 🇧🇪 BELGIUM - COMPACT SYSTEM (INACTIVE)
    # ==========================================
    "Belgium": {
        "active": False,         # 🚧 PREPARED FOR FUTURE
        "system": "compact",     # 14 teams, 26 rounds, 21.4% relegation
        "reputation": 74,        # Jupiler Pro League - decent level
        "leagues": [
            {
                "name": "Jupiler Pro League", # Tier 1
                "level": 1,
                "teams": 14
            },
            {
                "name": "Challenger Pro League", # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 14},  # Group 1
                    {"teams": 14},  # Group 2
                    {"teams": 14},  # Group 3
                    {"teams": 14}   # Group 4
                ]
            }
        ]
    },

    # ==========================================
    # 🇸🇪 SWEDEN - COMPACT SYSTEM (INACTIVE)
    # ==========================================
    "Sweden": {
        "active": False,         # 🚧 PREPARED FOR FUTURE
        "system": "compact",     # 14 teams, 26 rounds, 21.4% relegation
        "reputation": 70,        # Allsvenskan - average level
        "leagues": [
            {
                "name": "Allsvenskan",      # Tier 1
                "level": 1,
                "teams": 14
            },
            {
                "name": "Superettan",       # Tier 2 (grouped)
                "level": 2,
                "divisions": [
                    {"teams": 14},  # Group 1
                    {"teams": 14},  # Group 2
                    {"teams": 14},  # Group 3
                    {"teams": 14}   # Group 4
                ]
            }
        ]
    },

    # ==========================================
    # 🇳🇴 NORWAY - COMPACT SYSTEM (INACTIVE)
    # ==========================================
    "Norway": {
        "active": False,         # 🚧 PREPARED FOR FUTURE
        "system": "compact",     # 14 teams, 26 rounds, 21.4% relegation
        "reputation": 68,        # Eliteserien - average level
        "leagues": [
            {
                "name": "Eliteserien",      # Tier 1
                "level": 1,
                "teams": 14
            },
            {
                "name": "1. divisjon",      # Tier 2 (grouped)
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

# ==========================================
# 📊 CONFIGURATION SUMMARY
# ==========================================
"""
ACTIVE COUNTRIES (Beta Launch):
✅ England (Extended: 18 teams, reputation 92 - elite level)
✅ Denmark (Compact: 14 teams, reputation 75 - good level)

PREPARED COUNTRIES (Future Activation):
🚧 Germany (95), Spain (94), Italy (90), France (88), Netherlands (82)
🚧 Portugal (78), Belgium (74), Sweden (70), Norway (68)

REPUTATION SCALE (1-100):
90-100: Elite (Germany, Spain, Italy, England)
80-89:  Strong (France, Netherlands)
70-79:  Good (Denmark, Portugal, Belgium)
60-69:  Average (Sweden, Norway)
50-59:  Developing
40-49:  Weak
30-39:  Very Weak

DESIGN PRINCIPLES:
- Extended System: More matches, lower relegation risk, traditional big leagues
- Compact System: Faster seasons, higher intensity, smaller nations
- Dynamic reputation system ready for implementation
- All countries use consistent tier structure (Tier 1 + Tier 2 with 4 groups)
"""