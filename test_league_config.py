"""
test_league_config.py
---------------------
This script tests that league_config.py loads correctly.
It prints the configured nations, leagues, and divisions.
"""

from league_config import LEAGUE_CONFIG

print("✅ League Config Loaded Successfully!\n")

# Loop through nations and display details
for country_name, country_data in LEAGUE_CONFIG.items():
    print(f"🌍 {country_name} (Prestige: {country_data['prestige']})")

    for league in country_data["leagues"]:
        print(f"  🏆 {league['name']} (Tier {league['tier']})")

        if "teams" in league:
            print(f"    Teams: {league['teams']}")

        # If league has divisions (like League 2)
        if "divisions" in league:
            print("    Divisions:")
            for division in league["divisions"]:
                print(f"      - {division['name']} ({division['teams']} teams)")

    print()  # Blank line between countries
