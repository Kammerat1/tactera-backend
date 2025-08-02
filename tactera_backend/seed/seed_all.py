# seed_all.py
# Orchestrates all seed scripts to populate the database in the correct order, with detailed logging.

from tactera_backend.seed.seed_leagues import seed_leagues
from tactera_backend.seed.seed_clubs import seed_clubs
from tactera_backend.seed.seed_stadiums import seed_stadiums
from tactera_backend.seed.seed_traininggrounds import seed_traininggrounds
from tactera_backend.seed.seed_players import seed_players
from tactera_backend.seed.seed_player_stats import seed_player_stats
from tactera_backend.seed.seed_xp_levels import seed_xp_levels
from tactera_backend.seed.seed_season import seed_seasons
from tactera_backend.services.generate_fixtures import generate_fixtures_for_league

from sqlmodel import Session
from tactera_backend.core.database import sync_engine
from tactera_backend.models.league_model import League

def seed_all():
    print("\n🌱 Starting full database seeding...\n")

    print("➡️  Step 1: Seeding leagues...")
    seed_leagues()

    print("➡️  Step 2: Seeding training grounds...")
    seed_traininggrounds()  # ✅ Move this up!

    print("➡️  Step 3: Seeding clubs...")
    seed_clubs()

    print("➡️  Step 4: Seeding stadiums...")
    seed_stadiums()

    print("➡️  Step 5: Seeding players...")
    seed_players()

    print("➡️  Step 6: Seeding player stats...")
    seed_player_stats()

    print("➡️  Step 7: Seeding XP levels...")
    seed_xp_levels()

    print("➡️  Step 8: Seeding seasons...")
    seed_seasons()

    print("➡️  Step 9: Generating fixtures for all leagues...")
    with Session(sync_engine) as session:
        leagues = session.query(League).all()
        for league in leagues:
            print(f"   ⚽ Generating fixtures for {league.name}...")
            generate_fixtures_for_league(session, league.id)

    print("\n✅ Database seeding complete. All leagues initialized with fixtures.\n")

if __name__ == "__main__":
    seed_all()
